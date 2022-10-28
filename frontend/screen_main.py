# -*- coding: utf-8 -*-

from kivy.properties import (ObjectProperty, BooleanProperty, DictProperty, StringProperty)
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.navigationdrawer import MDNavigationDrawerItem
from kivymd.uix.label import MDLabel
from kivymd.color_definitions import colors
from kivy.clock import Clock
from kivymd.app import MDApp
from kivy.uix.button import Button
from typing import Any
from kivymd.uix.dialog.dialog import MDDialog

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .popup_progress import ProgressPopup
from .screen_courses import CourseBrowser
from .screen_grades import GradeChecker
from .screen_calendar import CalendarView
from .platform_specs import send_email

###############
#             #
# definitions #
#             #
###############

class MailMe(MDLabel):
    """
    Colorized label with the e-mail address of the author.
    """

    # name of the primary color paltte of the app
    primary_palette = StringProperty('')

    def on_ref_press(self, ref:str):
        """
        Called whenever user interacts with a markdown link.

        Positional arguments:
            ref: str,
                content of the markdown link.
        """

        # marked as accessed
        self.text = self.text.replace(
            "[ref={1}][color={0}]{1}[/color][/ref]".format(
                colors[self.primary_palette]['500'], ref
            ),
            "[ref={1}][color={0}]{1}[/color][/ref]".format(
                colors[self.primary_palette]['900'], ref
            )
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
    # static obervable storage for initialized screens (prevents unwanted garbage collection)
    subscreens = DictProperty({})
    # observeable app reference
    app = ObjectProperty(None)

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
        self.courses_btn.bind(on_release=self.go_courses)
        self.ids.md_drawer_menu.add_widget(self.courses_btn)

        self.grades_btn = NavigationItem(
            icon="format-list-numbered",
            text="Exam results",
        )
        self.grades_btn.bind(on_release=self.go_grades)
        self.ids.md_drawer_menu.add_widget(self.grades_btn)

        self.calendar_btn = NavigationItem(
            icon="calendar-month",
            text="Upcoming events",
        )
        self.calendar_btn.bind(on_release=self.go_calendar)
        self.ids.md_drawer_menu.add_widget(self.calendar_btn)

    @property
    def client(self) -> app.client:
        """
        Access point to the client interface.

        Returns:
            backend.Client
        """
        return self.app.client
        
    def on_enter(self, *args:tuple[Any]):
        """
        Called when entering the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to kivymd.uix.screen.MDScreen.on_enter method.
        """

        # switch to the courses screen
        self.go_courses(None)
        return super().on_enter(*args)

    def on_leave(self, *args:tuple[Any]):
        """
        Called when leaving the screen.

        Positional arguments:
            *args: tuple[Any],
                arguments forwarded to kivymd.uix.screen.MDScreen.on_leave method.
        """

        # clear all children of internal screen manager
        self.ids.sm.clear_widgets()
        return super().on_leave(*args)

    def reload(self, bound_instance:Button):
        """
        Reloads contents of current screen.
        use_cache property isbeing use to enforce retrieval of live data.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
                button instance bound to this method.
        """

        self.use_cache = False
        # screen has to implement refresh method!
        screen = self.ids.sm.get_screen(self.ids.sm.current)
        if hasattr(screen, 'refresh'):
            screen.refresh()
        self.use_cache = True

    def logout(self, bound_instance):
        """
        Performs sign-out and switches back to the login screen.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
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
                popup.schedule_auto_update(30, .1)
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

        def perfom_switch(dt:int):
            """
            Watch-dog observing the state of the progress popup.

            Positional arguments:
                dt: int
                    interval in seconds denoting the lookup frequency.
            """
            
            if popup.has_started and popup.exception == None:
                # child thread still running
                Clock.schedule_once(perfom_switch, dt)
            else:
                # child thread has finished
                if isinstance(popup.exception, Exception):
                    # display warning in the banner
                    self.ids.banner.text = [
                        "Sign out failed!",
                        "text=popup.exception.args[0][:1].upper()+popup.exception.args[0][1:]"+"."
                    ]
                    self.ids.banner.show()
                else:
                    # switch to the login screen
                    self.app.switch_login()

        # dispatch watch-dog
        perfom_switch(1)
        

    def go_courses(self, bound_instance):
        """
        Performs switch to the "courses" subscreen.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
                button instance bound to this method.
        """

        self.client.Debug("switching to the courses screen")
        try:
            self.ids.sm.get_screen("courses")
        except:
            self.client.warning("failed to retrieve courses screen, reinitializing")
            if not self.subscreens.get("courses"):
                self.subscreens["courses"] = CourseBrowser(name="courses", main_screen=self)
            self.ids.sm.add_widget(self.subscreens["courses"])
        finally:
            # close navigation drawer
            self.ids.nav_drawer.set_state(new_state='close')
            # switch over
            self.ids.sm.transition.direction = "down"
            self.ids.sm.switch_to(self.ids.sm.get_screen("courses"))

    def go_grades(self, bound_instance):
        """
        Performs switch to the "grades" subscreen.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
                button instance bound to this method.
        """
        
        self.client.Debug("switching to the grades screen")
        try:
            self.ids.sm.get_screen("grades")
        except:
            self.client.warning("failed to retrieve grades screen, reinitializing")
            if not self.subscreens.get("grades"):
                self.subscreens["grades"] = GradeChecker(name="grades", main_screen=self)
            self.ids.sm.add_widget(self.subscreens["grades"])
        finally:
            # close navigation drawer
            self.ids.nav_drawer.set_state(new_state='close')
            # choose transition direction
            if self.ids.sm.current == "calendar":
                self.ids.sm.transition.direction = "down"
            else:
                self.ids.sm.transition.direction = "up"
            # switch over
            self.ids.sm.switch_to(self.ids.sm.get_screen("grades"))

    def go_calendar(self, bound_instance):
        """
        Performs switch to the "calendar" subscreen.

        Positional arguments:
            bound_instance: kivy.uix.button.Button,
                button instance bound to this method.
        """

        self.client.Debug("switching to the grades screen")
        try:
            self.ids.sm.get_screen("calendar")
        except:
            self.client.warning("failed to retrieve calendar screen, reinitializing")
            if not self.subscreens.get("calendar"):
                self.subscreens["calendar"] = CalendarView(name="calendar", main_screen=self)
            self.ids.sm.add_widget(self.subscreens["calendar"])
        finally:
            # close navigation drawer
            self.ids.nav_drawer.set_state(new_state='close')
            # switch over
            self.ids.sm.transition.direction = "up"
            self.ids.sm.switch_to(self.ids.sm.get_screen("calendar"))
        
