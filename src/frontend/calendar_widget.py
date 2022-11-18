import re
from datetime import datetime
from typing import Any, Union

from kivy.input.motionevent import MotionEvent
from kivy.properties import ListProperty, StringProperty
from kivy.uix.button import Button
from kivymd.uix.button import MDFlatButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager

from . import calendar_toolbox as cal_data
from .popup_calendar import CalendarEvent

###############
#             #
# definitions #
#             #
###############


class ArrowButton(MDFlatButton):
    """
    Buttons used to navigate between months.
    """


class CalendarButton(Button):
    """
    Day button with attached calendar events.
    """

    # place holder for calendar events
    events = ListProperty([])
    # day label
    day = StringProperty("")

    def __init__(
        self, *, events: tuple[dict[str, str]], day: str, **kwargs: tuple[str, Any]
    ):
        self.events = events
        self.day = day
        super().__init__(**kwargs)

    def on_release(self):
        if self.events:
            self.popup = CalendarEvent(
                title=self.day, events=self.events, initial_tags=["*"]
            )
            self.popup.open()


class DayButton(CalendarButton):
    """
    Inherits CalendarButton.
    """


class DayNumButton(DayButton):
    """
    Marker for Mon - Fri.
    """


class DayNumWeekendButton(DayButton):
    """
    Marker for weekend days.
    """


class TodayButton(DayButton):
    """
    Marker for current date.
    """


class MonthYearLabel(MDLabel):
    """
    Label describing current year and month.
    """


class DayAbbrLabel(MDLabel):
    """
    Label for abbreviated day names.
    """


class DayAbbrWeekendLabel(DayAbbrLabel):
    """
    Label for abbreviated weekend day names.
    """


class ButtonsGrid(MDGridLayout):
    """
    Container for day buttons.
    """


class MonthsManager(MDScreenManager):
    """
    Internal screen manager.
    """


class CalendarWidget(MDRelativeLayout):
    """
    Basic calendar widget modified from
    https://bitbucket.org/xxblx/kivycalendar (X11/MIT License)
    by Oleg Kozlov (xxblx), 2015
    (https://xxblx.bitbucket.org/)
    """

    # current's screen label
    title = StringProperty("")

    def __init__(
        self,
        events: list[dict[str, Union[datetime, bytes]]] = [],
        *args: tuple[Any],
        **kwargs: dict[str, Any],
    ):
        """
        Sets up the initial screen.

        Positional arguments:
            events: list[dict[str, Union[datetime, bytes]]], optional,
            [{
                "summary": bytes,
                "description": bytes,
                "dtstart": datetime.datetime,
                "dtend": datetime.datetime,
                "location": bytes
            }, ...]

            *args: tuple[Any],
                arguments passed to MDRelativeLayout.

        Keyword arguments:
            **kwargs: dict[str, Any],
                arguments passed to MDRelativeLayout.
        """

        super().__init__(*args, **kwargs)
        self.events = events
        self.prepare_data()
        self.init_ui()

    def init_ui(self):
        """
        Iniializes the screen manager and the sets up the initial screen (current month).
        """

        left_arrow = ArrowButton(
            text="<", on_press=self.go_prev, pos_hint={"top": 1, "left": 0}
        )
        right_arrow = ArrowButton(
            text=">", on_press=self.go_next, pos_hint={"top": 1, "right": 1}
        )
        self.add_widget(left_arrow)
        self.add_widget(right_arrow)

        self.title_label = MonthYearLabel(text=self.title)
        self.add_widget(self.title_label)

        self.sm = MonthsManager()
        self.add_widget(self.sm)

        self.create_month_scr(self.quarter[1])

    def create_month_scr(self, month: int):
        """
        Creates screen with calendar for one month.

        Positional arguments:
            month: int.
        """

        scr = MDScreen()
        m = self.month_names_eng[self.active_date[1] - 1]
        scr.name = "%s-%s" % (m, self.active_date[2])  # e.g., March-2015

        grid_layout = ButtonsGrid()
        scr.add_widget(grid_layout)

        # generate day abbreviated names
        for i in range(7):
            if i >= 5:  # weekends
                lbl = DayAbbrWeekendLabel(text=self.days_abrs[i])
            else:  # work days
                lbl = DayAbbrLabel(text=self.days_abrs[i])
            grid_layout.add_widget(lbl)

        # setup buttons with day numbers
        for week in month:
            for day in week:
                text = str(day[0])
                events = [
                    event
                    for event in self.events
                    if day[2]
                    and datetime(
                        day=day[0], month=self.active_date[1], year=self.active_date[2]
                    ).date()
                    == event["dtstart"].date()
                ]
                if events:
                    text = (
                        "[size=20sp][color={0:02X}{1:02X}{2:02X}]".format(40, 245, 100)
                        + text
                        + f"[/color][/size][sup][size=10sp]({len(events)})[/size][/sup]"
                    )

                today = cal_data.today_date_list()
                kwargs = {
                    "text": text,
                    "events": events,
                    "day": f"{day[0]}-{m}-{self.active_date[2]}",
                }
                if all(
                    [
                        day[0] == today[0],
                        self.active_date[1] == today[1],
                        self.active_date[2] == today[2],
                        day[2] == 1,
                    ]
                ):
                    tbtn = TodayButton(**kwargs)
                elif day[1] >= 5:  # weekends
                    tbtn = DayNumWeekendButton(**kwargs)
                else:  # work days
                    tbtn = DayNumButton(**kwargs)

                tbtn.bind(on_press=self.get_btn_value)

                # Disable buttons with days from other months
                if not day[2]:
                    tbtn.disabled = True

                grid_layout.add_widget(tbtn)

        self.sm.add_widget(scr)

    def prepare_data(self):
        """
        Prepare data for showing on widget loading.
        """

        # Get day abbreviated names and month names lists
        self.month_names_eng = cal_data.get_month_names_eng()
        self.days_abrs = cal_data.get_days_abbrs()

        # today date
        self.active_date = cal_data.today_date_list()
        # set title
        self.title = "%s - %s" % (
            self.month_names_eng[self.active_date[1] - 1],
            self.active_date[2],
        )

        # quarter where current month is in
        self.get_quarter()

    def get_quarter(self):
        """
        Get caledar and month/year numbers for current quarter.
        """

        self.quarter_nums = cal_data.calc_quarter(*self.active_date[::-1][:2])
        self.quarter = cal_data.get_quarter(*self.active_date[::-1][:2])

    def get_btn_value(self, inst):
        """
        Get day value from pressed button
        """

        # strip markdown formatters
        self.active_date[0] = int(re.sub(r"\[.*?\]|\(.*?\)", "", inst.text))

    def go_prev(self, bound_instance: Button):
        """
        Go to the screen displaying previous month.

        Positional arguments:
            bound_instance: Button,
                button bount to the method.
        """

        # Change active date
        self.active_date = [
            self.active_date[0],
            self.quarter_nums[0][1],
            self.quarter_nums[0][0],
        ]

        # Name of previous screen
        prev_scr_name = "%s-%s" % (
            self.month_names_eng[self.quarter_nums[0][1] - 1],
            self.quarter_nums[0][0],
        )

        # If it's doen't exists, create it
        if not self.sm.has_screen(prev_scr_name):
            self.create_month_scr(self.quarter[0])

        self.sm.current = prev_scr_name
        self.sm.transition.direction = "right"

        self.get_quarter()
        self.title = "%s - %s" % (
            self.month_names_eng[self.active_date[1] - 1],
            self.active_date[2],
        )

        self.title_label.text = self.title

    def go_next(self, inst):
        """
        Go to the screen displaying next month.

        Positional arguments:
            bound_instance: Button,
                button bount to the method.
        """

        # Change active date
        self.active_date = [
            self.active_date[0],
            self.quarter_nums[2][1],
            self.quarter_nums[2][0],
        ]

        # Name of previous screen
        next_scr_name = "%s-%s" % (
            self.month_names_eng[self.quarter_nums[2][1] - 1],
            self.quarter_nums[2][0],
        )

        # If it's doen't exists, create it
        if not self.sm.has_screen(next_scr_name):
            self.create_month_scr(self.quarter[2])

        self.sm.current = next_scr_name
        self.sm.transition.direction = "left"

        self.get_quarter()
        self.title = "%s - %s" % (
            self.month_names_eng[self.active_date[1] - 1],
            self.active_date[2],
        )

        self.title_label.text = self.title

    def on_touch_move(self, touch: MotionEvent):
        """
        Switch months pages by touch move.

        Positional arguments:
            touch: MotionEvent,
                touch event.
        """

        # left - previous
        if touch.dpos[0] < -30:
            self.go_prev(None)
        # right - next
        elif touch.dpos[0] > 30:
            self.go_next(None)
