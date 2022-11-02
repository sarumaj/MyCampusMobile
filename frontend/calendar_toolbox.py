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

from calendar import month_name, day_abbr, Calendar, monthrange
from datetime import datetime
       
def get_month_names_eng():
    return [month_name[i] for i in range(1, 13)]

def get_days_abbrs():
    return [day_abbr[i] for i in range(7)]

def calc_quarter(y, m):
    """ Calculate previous and next month """
    
    prev_y, prev_m = y, m - 1
    next_y, next_m = y, m + 1  
    
    if m == 1:
        prev_m = 12
        prev_y = y - 1
    elif m == 12:
        next_m = 1
        next_y = y + 1
        
    return [(prev_y, prev_m), (y, m), (next_y, next_m)]

def get_month(y, m):
    """ 
    Returns tuple (<month day number>, <weekday number>, <month: 1 if current 0 else>) 
    """
    
    cal = Calendar()   
    month = [
        [
            (
                day[0], # month day number (0 if day doesn't belong to current month)
                day[1], # weekday number: 0 - Monday
                False if day[0] == 0 else True # month: 1: current
            ) for day in week
        ] for week in cal.monthdays2calendar(y, m)
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
                monthrange(
                    *calc_quarter(y, m)[0][:2] # index 0: previous month
                )[1] - ( # index 1: month
                    fcount - 1 - i # decrease day number
                ), i, False
            )
            
    if lcount:
        # update day numbers from the next month
        for i in range(lcount):
            month[-1][-lcount + i] = (1 + i, 7 - lcount + i, False)
            
    return month

def get_quarter(y, m):
    return [get_month(*i[:2]) for i in calc_quarter(y, m)]

def today_date_list():
   return [datetime.now().day, datetime.now().month, datetime.now().year]
    
def today_date():
    return datetime.now().strftime("%d.%m.%Y")