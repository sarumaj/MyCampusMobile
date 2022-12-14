# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import DictProperty, ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar

from .calendar_widget import CalendarWidget
from .popup_calendar import CalendarEvent
from .popup_save_dialog import SaveDialog

Builder.load_string(
    r"""
#:kivy 2.1.0

<CalendarView>:
    MDBanner:
        id: banner
        text: []
        over_widget: root
        vertical_pad: root.main_screen.ids.top_bar.height - self.height
        type: "two-line"
        right_action: ["CLOSE", lambda bound_instance: self.hide()]

    MDScrollView:
        id: table_layout
        size_hint: (1, 1)
        do_scroll_x: False
        do_scroll_y: True
        scroll_type: ['bars', 'content']
"""
)

###############
#             #
# definitions #
#             #
###############


class Client:
    pass


class CalendarView(MDScreen):
    # name of the ical file used for export
    filename = StringProperty("")
    # container for calendar events
    events = DictProperty({})
    # reference to the "main" screen
    main_screen = ObjectProperty(None)

    def __init__(self, *, main_screen: MDScreen, **kwargs: dict[str, Any]):
        """
        Creates calendar view.

        Keyword arguments:
            main_screen: kivymd.uix.screen.MDScreen,
                reference to the "main" screen instance.

            **kwargs: dict[str,Any],
                keyword arguments passed to the MDScreen class.
        """

        self.main_screen = main_screen
        super().__init__(**kwargs)
        self.get_events()

    @property
    def client(self) -> Client:
        return self.main_screen.client

    @property
    def top_bar(self) -> MDTopAppBar:
        return self.main_screen.ids.top_bar

    @property
    def use_cache(self) -> bool:
        return self.main_screen.use_cache

    @use_cache.setter
    def use_cache(self, value: bool):
        self.main_screen.use_cache = value

    def on_enter(self, *args):
        """
        Called when entering the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to kivymd.uix.screen.MDScreen.on_enter method.
        """

        super().on_enter(*args)
        self.top_bar.title = "Recent & upcoming events"
        # list of temporary top panel entries
        self.to_remove = [
            [
                "calendar-export-outline",
                self.export,
                "Export calendar events",
                "Export calendar events",
            ],
            [
                "calendar-search-outline",
                self.search,
                "Search calendar events",
                "Search calendar events",
            ],
        ]
        # extend top bar of "main" screen
        for item in self.to_remove:
            if item not in self.top_bar.right_action_items:
                self.top_bar.right_action_items.insert(0, item)

    def on_leave(self, *args):
        """
        Called when leaving the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to kivymd.uix.screen.MDScreen.on_leave method.
        """

        # remove temporary top panel entries
        for item in self.to_remove:
            try:
                self.top_bar.right_action_items.remove(item)
            except ValueError:
                pass
        return super().on_leave(*args)

    def get_events(self):
        """
        Method collects calendar events via Client interface.
        """

        try:
            self.filename, self.events = self.client.export_calendar(
                cached=self.use_cache
            )
        except BaseException as ex:
            self.ids.banner.text = [
                "Failed to import calendar events!",
                ex.args[0][:1].upper() + ex.args[0][1:] + ".",
            ]
            self.ids.banner.show()
        else:
            self.ids.table_layout.add_widget(
                CalendarWidget(events=self.events["parsed"])
            )
            self.main_screen.calendar_btn.right_text = f"({len(self.events['parsed'])})"

    def refresh(self):
        """
        Method enforces refreshment of the data and displayed widgets.
        """

        def refresh_callback(interval):
            self.ids.table_layout.clear_widgets()
            self.use_cache = False
            self.get_events()
            self.use_cache = True

        Clock.schedule_once(refresh_callback, 1)

    def export(self, bound_instance: Button):
        """
        Method dispatches a save file dialog to save exported calendar events in the ical format.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
                button instance bound to this widget.
        """

        spopup = SaveDialog(
            content_disposition=self.filename,
            save_method=lambda file, path: self.client.save(
                file, self.events["ical"], Path(path)
            ),
            banner=self.ids.banner,
        )
        spopup.open()

    def search(self, bound_instance: Button):
        """
        Method dispatches a dialog displaying filtered calendar events.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
                button instance bound to this widget.
        """

        popup = CalendarEvent(
            title="Search calendar events",
            initial_tags=[],
            events=self.events["parsed"],
        )
        popup.open()
