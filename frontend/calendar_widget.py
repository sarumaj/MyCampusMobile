from kivymd.uix.screen import MDScreen
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.properties import (StringProperty, ListProperty)
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDFlatButton
from kivy.uix.button import Button
from kivymd.uix.label import MDLabel
from datetime import datetime
import re

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[2]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from . import calendar_toolbox as cal_data
from .popup_calendar import CalendarEvent

###############
#             #
# definitions #
#             #
###############

class ArrowButton(MDFlatButton):
    pass

class CalendarButton(Button):
    events = ListProperty([])
    day = StringProperty('')

    def __init__(self, **kwargs):
        self.events = kwargs.pop('events')
        self.day = kwargs.pop('day')
        super().__init__(**kwargs)

    def on_release(self):
        if self.events:
            self.popup = CalendarEvent(title=self.day, events=self.events, initial_tags=['*'])
            self.popup.open()


class DayButton(CalendarButton):
    pass

class DayNumButton(DayButton):
    pass

class DayNumWeekendButton(DayButton):
    pass

class TodayButton(DayButton):
    pass

class MonthYearLabel(MDLabel):
    pass

class DayAbbrLabel(MDLabel):
    pass

class DayAbbrWeekendLabel(DayAbbrLabel):
    pass

class ButtonsGrid(MDGridLayout):
    pass

class MonthsManager(MDScreenManager):
    pass

class CalendarWidget(MDRelativeLayout):
    title = StringProperty('')
    """ 
    Basic calendar widget modified from 
    https://bitbucket.org/xxblx/kivycalendar (X11/MIT License)
    by Oleg Kozlov (xxblx), 2015 
    (https://xxblx.bitbucket.org/)
    """
    
    def __init__(self, events=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.events = events
        self.prepare_data()     
        self.init_ui()
        
    def init_ui(self):
        left_arrow = ArrowButton(
            text="<", on_press=self.go_prev,
            pos_hint={"top": 1, "left": 0}
        )
        
        right_arrow = ArrowButton(
            text=">", on_press=self.go_next,
            pos_hint={"top": 1, "right": 1}
        )
        
        self.add_widget(left_arrow)        
        self.add_widget(right_arrow)
          
        self.title_label = MonthYearLabel(text=self.title)
        self.add_widget(self.title_label)
        
        self.sm = MonthsManager()
        self.add_widget(self.sm)
        
        self.create_month_scr(self.quarter[1]) 
    
    def create_month_scr(self, month):
        """ Screen with calendar for one month """        
        
        scr = MDScreen()
        m = self.month_names_eng[self.active_date[1] - 1]
        scr.name = "%s-%s" % (m, self.active_date[2])  # e.g., March-2015

        grid_layout = ButtonsGrid()
        scr.add_widget(grid_layout)
        
        # Days abbrs 
        for i in range(7):
            if i >= 5:  # weekends
                l = DayAbbrWeekendLabel(text=self.days_abrs[i])
            else:  # work days
                l = DayAbbrLabel(text=self.days_abrs[i])
            grid_layout.add_widget(l)
            
        # Buttons with days numbers
        for week in month:
            for day in week:
                text = str(day[0])
                events = [
                    event for event in self.events if day[2] and datetime(
                        day=day[0],
                        month=self.active_date[1],
                        year=self.active_date[2]
                    ).date() == event['dtstart'].date()
                ]
                if events:
                    text = "[size=20sp][color={0:02X}{1:02X}{2:02X}]{3}[/color][/size][sup][size=10sp]({4})[/size][/sup]".format(
                        40, 245, 100, 
                        text, len(events)
                    )

                today = cal_data.today_date_list()
                kwargs = {
                    "text": text,
                    "events": events,
                    "day": f"{day[0]}-{m}-{self.active_date[2]}"
                }
                if all([
                    day[0] == today[0],
                    self.active_date[1] == today[1],
                    self.active_date[2] == today[2],
                    day[2] == 1
                ]):
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
        """ Prepare data for showing on widget loading """
    
        # Get days abbrs and month names lists 
        self.month_names_eng = cal_data.get_month_names_eng()
        self.days_abrs = cal_data.get_days_abbrs() 

        
        # Today date
        self.active_date = cal_data.today_date_list()
        # Set title
        self.title = "%s - %s" % (
            self.month_names_eng[self.active_date[1] - 1], 
            self.active_date[2]
        )
                
        # Quarter where current month in the self.quarter[1]
        self.get_quarter()
    
    def get_quarter(self):
        """ Get caledar and months/years nums for quarter """
        
        self.quarter_nums = cal_data.calc_quarter(*self.active_date[::-1][:2])
        self.quarter = cal_data.get_quarter(*self.active_date[::-1][:2])
    
    def get_btn_value(self, inst):
        """ Get day value from pressed button """
        
        self.active_date[0] = int(re.sub('\[.*?\]|\(.*?\)', '', inst.text))
                
    def go_prev(self, inst):
        """ Go to screen with previous month """        

        # Change active date
        self.active_date = [
            self.active_date[0], 
            self.quarter_nums[0][1], 
            self.quarter_nums[0][0]
        ]

        # Name of previous screen
        prev_scr_name = "%s-%s" % (
            self.month_names_eng[self.quarter_nums[0][1] - 1], 
            self.quarter_nums[0][0]
        )
        
        # If it's doen't exists, create it
        if not self.sm.has_screen(prev_scr_name):
            self.create_month_scr(self.quarter[0])
            
        self.sm.current = prev_scr_name
        self.sm.transition.direction = "right"
        
        self.get_quarter()
        self.title = "%s - %s" % (
            self.month_names_eng[self.active_date[1] - 1], 
            self.active_date[2]
        )
        
        self.title_label.text = self.title
    
    def go_next(self, inst):
        """ Go to screen with next month """
        
         # Change active date
        self.active_date = [
            self.active_date[0], 
            self.quarter_nums[2][1], 
            self.quarter_nums[2][0]
        ]

        # Name of previous screen
        next_scr_name = "%s-%s" % (
            self.month_names_eng[self.quarter_nums[2][1] - 1], 
            self.quarter_nums[2][0]
        )
        
        # If it's doen't exists, create it
        if not self.sm.has_screen(next_scr_name):
            self.create_month_scr(self.quarter[2])
            
        self.sm.current = next_scr_name
        self.sm.transition.direction = "left"
        
        self.get_quarter()
        self.title = "%s - %s" % (
            self.month_names_eng[self.active_date[1] - 1], 
            self.active_date[2]
        )
        
        self.title_label.text = self.title
        
    def on_touch_move(self, touch):
        """ Switch months pages by touch move """
                
        # Left - previous
        if touch.dpos[0] < -30:
            self.go_prev(None)
        # Right - next
        elif touch.dpos[0] > 30:
            self.go_next(None)
        
