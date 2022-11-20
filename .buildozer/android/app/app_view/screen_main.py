# -*- coding: utf-8 -*-

from typing import Any

import asynckivy
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.button import Button
from kivymd.app import MDApp
from kivymd.color_definitions import colors
from kivymd.uix.dialog.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.navigationdrawer import MDNavigationDrawerItem
from kivymd.uix.screen import MDScreen

from .platform_specs import send_email
from .popup_progress import ProgressPopup
from .screen_calendar import CalendarView
from .screen_courses import CourseBrowser
from .screen_grades import GradeChecker

Builder.load_string(
    r"""
#:kivy 2.1.0
# import  kivymd.color_definitions.colors colors

<MailMe>:
    primary_palette: app.theme_cls.primary_palette

<NavigationItem>:
    focus_color: app.theme_cls.primary_dark
    text_color: app.theme_cls.text_color
    text_right_color: app.theme_cls.text_color
    icon_color: app.theme_cls.text_color
    ripple_color: app.theme_cls.primary_color
    selected_color: app.theme_cls.accent_color
    
<MainScreenWithTopPanel>:
    BoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            id: top_bar
            use_overflow: True
            left_action_items: 
                [
                ['menu', lambda x: nav_drawer.set_state("close") if nav_drawer.state == 'open' else nav_drawer.set_state("open")],
                ]
            right_action_items: 
                [
                ["reload", root.reload, *(["Refresh"]*2)], 
                ["logout-variant", root.logout, *(["Sign out"]*2)]
                ]

        MDNavigationLayout:
            id: main_layout
            size_hint: (1, None)
            height: Window.height - top_bar.height

            MDScreenManager:
                id: sm

            MDNavigationDrawer:
                id: nav_drawer
                type: "standard"
                radius: (0, 16, 16, 0)
                close_on_click: True
                enable_swiping: True

                MDNavigationDrawerMenu:
                    id: md_drawer_menu

                    MDBoxLayout:
                        orientation: "vertical"
                        size_hint: (1, None)
                        pos_hint: {'center_x':.5, }
                        adaptive_height: True
                        spacing: dp(20)

                        MDBoxLayout:
                            orientation: 'horizontal'
                            pos_hint: {'center_x':.5}
                            spacing: dp(10)
                            height: dp(100)
                            size_hint: (1, None)

                            FitImage:
                                id: logo
                                source: app.theme_cls.custom_logo
                                size: (dp(100), dp(100))
                                size_hint: (None, None)
                                text_size: self.size
                                halign: 'right'
                                valign: 'middle'

                            MDLabel:
                                text: "INTERNATIONAL\nUNIVERSITY\nOF APPLIED SCIENCES"
                                font_size: '20sp'
                                text_size: self.size
                                height: self.texture_size[1]
                                size_hint: (1, None)
                                halign: 'left'
                                valign: 'bottom'
                                theme_text_color: "Custom"
                                text_color: app.theme_cls.opposite_bg_normal

                        MDLabel:
                            text: "MyCampus Mobile"
                            font_size: '20sp'
                            text_color: app.theme_cls.primary_dark
                            theme_text_color: "Custom"
                            height: self.texture_size[1]
                            text_size: self.size
                            size_hint:(1, None)
                            halign: 'center'
                            valign: 'bottom'

                        MailMe:
                            text: f"Contact: [u][ref=dawid.ciepiela@iu-study.org][color={colors[app.theme_cls.primary_palette]['500']}]dawid.ciepiela@iu-study.org[/color][/ref][/u]"
                            font_style: "Caption"
                            size_hint_y: None
                            font_size: '12sp'
                            height: self.texture_size[1]
                            halign: 'center'
                            valign: 'bottom'
                            markup: True

                    MDNavigationDrawerDivider:

                    MDNavigationDrawerLabel:
                        text: "Navigate"
"""
)

###############
#             #
# definitions #
#             #
###############


class Client:
    pass


class MailMe(MDLabel):
    """
    Colorized label with the e-mail address of the author.
    """

    # name of the primary color paltte of the app
    primary_palette = StringProperty("")

    def on_ref_press(self, ref: str):
        """
        Called whenever user interacts with a markdown link.

        Positional arguments:
            ref: str,
                content of the markdown link.
        """

        # marked as accessed
        self.text = self.text.replace(
            "[ref={1}][color={0}]{1}[/color][/ref]".format(
                colors[self.primary_palette]["500"], ref
            ),
            "[ref={1}][color={0}]{1}[/color][/ref]".format(
                colors[self.primary_palette]["900"], ref
            ),
        )
        # dispatch default e-mail client
        send_email(ref)
        return super().on_ref_press(ref)


class NavigationItem(MDNavigationDrawerItem):
    """
    Item for the navigation drawer.
    """


class MainScreenWithTopPanel(MDScreen):
    """
    Main screen extending kivymd.uix.screen.MDScreen.
    """

    # determines whether client actions should return live or cached data
    use_cache = BooleanProperty(True)
    # observeable app reference
    app = ObjectProperty(None)
    # reference to asynchronous content loader
    # to track the content loading routine
    asyncloader = ObjectProperty(None)
    # flag
    loaded = BooleanProperty(False)
    # static obervable storage for initialized screens (prevents unwanted garbage collection)
    subscreens = DictProperty({})

    def __init__(self, *, app: MDApp, **kwargs):
        """
        Create main window.

        Keyword arguments:
            app: kivymd.app.MDApp
                observable reference of the MDApp instance.

            **kwargs: dict[str,Any]
                keyword arguments supported by the parent class kivymd.uix.screen.MDScreen.
        """

        self.app = app
        super().__init__(**kwargs)

        # define items for navigation drawer
        self.courses_btn = NavigationItem(
            icon="home-group-plus",
            text="Course access",
        )
        self.courses_btn._text_color = self.courses_btn.text_color
        self.courses_btn.selected = True
        self.courses_btn.bind(on_release=lambda btn_inst: self.switch_screen("courses"))
        self.ids.md_drawer_menu.add_widget(self.courses_btn)

        self.grades_btn = NavigationItem(
            icon="format-list-numbered",
            text="Exam results",
        )
        self.grades_btn.bind(on_release=lambda btn_inst: self.switch_screen("grades"))
        self.ids.md_drawer_menu.add_widget(self.grades_btn)

        self.calendar_btn = NavigationItem(
            icon="calendar-month",
            text="Upcoming events",
        )
        self.calendar_btn.bind(
            on_release=lambda btn_inst: self.switch_screen("calendar")
        )
        self.ids.md_drawer_menu.add_widget(self.calendar_btn)

    @property
    def client(self) -> Client:
        """
        Access point to the client interface.

        Returns:
            backend.Client
        """
        return self.app.client

    def on_enter(self, *args: tuple[Any]):
        """
        Called when entering the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to MDScreen.on_enter method.
        """

        # load all subscreens
        if not self.loaded:
            self.load_screens()
        return super().on_enter(*args)

    def reload(self, bound_instance: Button):
        """
        Reloads contents of current screen.
        use_cache property isbeing use to enforce retrieval of live data.

        Positional arguments:
            bound_instance: Button,
                button instance bound to this method.
        """

        self.use_cache = False
        # screen has to implement refresh method!
        screen = self.ids.sm.get_screen(self.ids.sm.current)
        if hasattr(screen, "refresh"):
            screen.refresh()
        self.use_cache = True

    def logout(self, bound_instance):
        """
        Performs sign-out and switches back to the login screen.

        Positional arguments:
            bound_instance: Button,
                button instance bound to this method.
        """

        # explicitly trigger on_leave event to clear user content
        self.on_leave()
        # dispatch progress popup
        popup = ProgressPopup(title="Signing out...")
        popup.open()

        def perform_logout(self, popup: MDDialog):
            """
            Worker perfoming sign-in actions and updating the state of the progress popup.

            Positional arguments:
                popup: kivymd.uix.dialog.dialog.MDDialog
                    custom popup displaying progress of the sign-in procedure.
            """

            try:
                # dispatch auto update of the progress bar
                popup.schedule_auto_update(30, 0.1)
                # set status message
                popup.status_msg = "Signing out..."
                # perform sign-out
                self.client.close()
                # finished
                popup.prog_val = 100

            except BaseException as ex:
                # pass exception to the popup instance
                popup.exception = ex

            finally:
                popup.dismiss()

        # dispatch coroutine as child thread
        popup.run_worker(perform_logout, self, popup)

        def perfom_switch(dt: int):
            """
            Watch-dog observing the state of the progress popup.

            Positional arguments:
                dt: int
                    interval in seconds denoting the lookup frequency.
            """

            if popup.has_started and popup.exception is None:
                # child thread still running
                Clock.schedule_once(perfom_switch, dt)
            else:
                # child thread has finished
                if isinstance(popup.exception, Exception):
                    # display warning in the banner
                    self.ids.banner.text = [
                        "Sign out failed!",
                        "text=popup.exception.args[0][:1].upper()+popup.exception.args[0][1:]"
                        + ".",
                    ]
                    self.ids.banner.show()
                else:
                    # clear all children of internal screen manager
                    self.ids.sm.clear_widgets()
                    # reset flag
                    self.loaded = False
                    # switch to the login screen
                    self.app.switch_login()

        # dispatch watch-dog
        perfom_switch(1)

    def load_screens(self):
        """
        Performs switch to the "grades" subscreen.
        """

        views = {
            "courses": {"no": 0, "class": CourseBrowser},
            "grades": {"no": 1, "class": GradeChecker},
            "calendar": {"no": 2, "class": CalendarView},
        }

        async def load_screen(name: str, teardown: bool):
            """
            Asynchronous task to load a screen given by name.
            """
            try:
                self.ids.sm.get_screen(name)
            except BaseException:
                if not self.subscreens.get(name):
                    self.subscreens[name] = views[name]["class"](
                        name=name, main_screen=self
                    )
                self.ids.sm.add_widget(self.subscreens[name])
            finally:
                # close navigation drawer
                self.ids.nav_drawer.set_state(new_state="close")
                # choose transition direction
                if views[name]["no"] <= views.get(self.ids.sm.current, {}).get("no", 0):
                    self.ids.sm.transition.direction = "down"
                else:
                    self.ids.sm.transition.direction = "up"
                # trigger initialization
                self.ids.sm.get_screen(name).on_enter()
                # tear down
                if teardown:
                    self.ids.sm.get_screen(name).on_leave()

        async def load_screens():
            """
            Cumulative task to dispatch loading tasks in order and switch to the initial subscreen.
            """

            # async caller to switch to the inital subscreen
            async def switch():
                self.switch_screen("courses")

            # dispatch content loaders (order matters!)
            for screen in ("calendar", "grades", "courses"):
                await load_screen(screen, True)
            # switch over
            await switch()

        if self.asyncloader is not None and not self.asyncloader.done:
            self.asyncloader.cancel()
        self.asyncloader = asynckivy.start(load_screens())
        self.loaded = True

    def switch_screen(self, name: str):
        """
        Performs switch to given subscreen.

        Positional arguments:
            name: str,
                screen name.
        """

        views = {
            "courses": {"no": 0, "class": CourseBrowser},
            "grades": {"no": 1, "class": GradeChecker},
            "calendar": {"no": 2, "class": CalendarView},
        }
        self.client.debug(f"switching to the {name} screen")
        try:
            self.ids.sm.get_screen(name)
        except BaseException:
            self.client.warning(f"failed to retrieve {name} screen, reinitializing")
            if not self.subscreens.get(name):
                self.subscreens[name] = views[name]["class"](
                    name=name, main_screen=self
                )
            self.ids.sm.add_widget(self.subscreens[name])
        finally:
            # close navigation drawer
            self.ids.nav_drawer.set_state(new_state="close")
            # choose transition direction
            if views[name]["no"] <= views.get(self.ids.sm.current, {}).get("no", 0):
                self.ids.sm.transition.direction = "down"
            else:
                self.ids.sm.transition.direction = "up"
            # switch over
            self.ids.sm.switch_to(self.ids.sm.get_screen(name))
