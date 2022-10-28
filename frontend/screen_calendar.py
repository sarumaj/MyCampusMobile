# -*- coding: utf-8 -*-

from kivy.properties import (ObjectProperty, StringProperty)
from kivymd.uix.screen import (MDScreen)
from pathlib import Path

from screen_navbar import ScreenWithNavBar
from navbar import MenuItem
from popup_notifier import Notifier
from calendar_widget import CalendarWidget
from popup_save_dialog import SaveDialog
from popup_calendar import CalendarEvent

class CalendarView(MDScreen):
    filename = StringProperty('')
    events = ObjectProperty('')
    master = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.master = kwargs.pop('master')
        super().__init__(**kwargs)
        self.get_events()

    def on_enter(self, *args):
        super().on_enter(*args)
        self.master.ids.top_bar.title = "Recent & upcoming events"
        self.to_remove = [
            ['calendar-export-outline', self.export, 'Export calendar events', 'Export calendar events'],
            ['calendar-search-outline', self.search, 'Search calendar events', 'Search calendar events']
        ]
        for item in self.to_remove:
            if item not in self.master.ids.top_bar.right_action_items:
                self.master.ids.top_bar.right_action_items.insert(0, item)
        
    def get_events(self):
        try:
            fname, events = self.master.manager.client.export_calendar(cached=self.master.use_cache)
            self.filename = fname
            self.events = events
        except BaseException as ex:
            self.ids.banner.text = [
                "Failed to import calendar events!",
                ex.args[0][:1].upper()+ex.args[0][1:]+"."
            ]
            self.ids.banner.show()
        finally:
            self.ids.table_layout.add_widget(CalendarWidget(events=self.events['parsed']))
            self.master.calendar_btn.right_text = f"({len(self.events['parsed'])})"


    def on_leave(self, *args):
        for item in self.to_remove:
            self.master.ids.top_bar.right_action_items.remove(item)
        return super().on_leave(*args)

    def refresh(self):
        self.ids.table_layout.clear_widgets()
        self.master.use_cache = False
        self.get_events()
        self.master.use_cache = True

    def export(self, bound_instance):
        spopup = SaveDialog(
            content_disposition=self.filename, 
            save_method=lambda file, path: self.master.manager.client.save(
                file, self.events['ical'], Path(path)
            ),
            banner=self.ids.banner
        )
        spopup.open()

    def search(self, bound_instance):
        popup = CalendarEvent(
            title="Search calendar events", 
            events=self.events['parsed']
        )
        popup.open()