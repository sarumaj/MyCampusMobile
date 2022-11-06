# -*- coding: utf-8 -*-

###########################################################
# Modified contents of:                                   #
# KivyCalendar (X11/MIT License)                          #
# Calendar widget for Kivy (http://kivy.org)              #
# https://bitbucket.org/xxblx/kivycalendar                #
#                                                         #
# Oleg Kozlov (xxblx), 2015                               #
# https://xxblx.bitbucket.org/                            #
###########################################################

from calendar import Calendar, day_abbr, month_name, monthrange
from datetime import datetime
from typing import Union


def get_month_names_eng() -> list[str]:
    """
    Returns month names.

    Returns:
        list[str]
    """

    return [month_name[i] for i in range(1, 13)]


def get_days_abbrs() -> list[str]:
    """
    Returns day abbreviated names.

    Returns:
        list[str]
    """

    return [day_abbr[i] for i in range(7)]


def calc_quarter(y: int, m: int) -> list[tuple[int]]:
    """
    Returns months surrounding given month.

    Positional arguments:
        y: int,
            given year.

        m: int,
            given month.

    Returns
        list[tuple[int]],
        [
            (year, previous_month),
            (given_year, given_month),
            (year, next_month)
        ]
    """

    return [
        m == 1 and (y - 1, 12) or (y, m - 1),
        (y, m),
        (m == 12) and (y + 1, 1) or (y, m + 1),
    ]


def get_month(y: int, m: int) -> list[tuple[Union[int, bool]]]:
    """
    Generates a list of month days.

    Positional arguments:
        y: int,
            given year.

        m: int,
            given month.

    Returns:
        list[tuple[Union[int, bool]]]:
        [
            (
                <month day number>,
                <weekday number (0 - Monday)>,
                <True if day belongs to given month else False>
            ),
            ...
        ]
    """

    cal = Calendar()
    month = [
        [
            (
                day[0],  # month day number (0 if day doesn't belong to current month)
                day[1],  # weekday number: 0 - Monday
                False if day[0] == 0 else True,  # is current month?
            )
            for day in week
        ]
        for week in cal.monthdays2calendar(y, m)
    ]

    # Count days from the previous month
    fcount = len([day for day in month[0] if day[0] == 0])
    # Count days from the next month
    lcount = len([day for day in month[-1] if day[0] == 0])

    if fcount:
        # update day numbers from previous month
        # get last day of previous month
        for i in range(fcount):
            month[0][i] = (
                monthrange(*calc_quarter(y, m)[0][:2])[1]  # index 0: previous month
                - (fcount - 1 - i),  # index 1: month  # decrease day number
                i,
                False,
            )

    if lcount:
        # update day numbers from the next month
        for i in range(lcount):
            month[-1][-lcount + i] = (1 + i, 7 - lcount + i, False)

    return month


def get_quarter(y: int, m: int) -> list[list[tuple[Union[int, bool]]]]:
    """
    Generates month day list for whole quarter.

    Positional arguments:
        y: int,
            given year.

        m: int,
            given month.

    Returns:
        list[list[tuple[Union[int, bool]]]],
        [
            get_month(year, previous_month),
            get_month(given_year, given_month),
            get_month(year, next_month)
        ]
    """

    return [get_month(*i[:2]) for i in calc_quarter(y, m)]


def today_date_list() -> list[int]:
    """
    Returns today's date as list.

    Returns:
        list[int],
        [
            <day>, <month>, <year>
        ]
    """

    return [datetime.now().day, datetime.now().month, datetime.now().year]


def today_date() -> str:
    """
    Returns today's date in dd-mm-yyyy format.

    Returns:
        str
    """

    return datetime.now().strftime("%d.%m.%Y")
