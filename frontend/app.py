# -*- coding: utf-8 -*-

from kivymd.app import MDApp
from kivy.uix.screenmanager import SlideTransition
from kivymd.uix.screenmanager import MDScreenManager
from kivy.properties import (
    DictProperty, ObjectProperty, StringProperty, NumericProperty
)

from pathlib import Path

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

from .screen_login import LoginWindow
from .screen_main import MainScreenWithTopPanel

###############
#             #
# definitions #
#             #
###############

class WindowManager(MDScreenManager):
    """
    Custom screen manager.
    """

    # numeric property used to store course id
    selected_course_id = NumericProperty(0)
    # string property used to store course name
    selected_course_name = StringProperty('')

class MobileApp(MDApp):
    """
    Application object.
    """

    title = "MyCampus Mobile"
    icon = "data/dark.png"

    # static obervable storage for initialized screens (prevents unwanted garbage collection)
    screens = DictProperty({})
    # observable client object
    client = ObjectProperty(None)

    def switch_login(self):
        """
        Trigger ScreenManager to switch to the "login" screen.
        """

        try:
            self.sm.get_screen("login")
        except:
            if not self.screens.get("login"):
                self.screens["login"] = LoginWindow(name="login", app=self)
            self.sm.add_widget(self.screens["login"])
        finally:
            self.sm.transition.direction = "right"
            self.sm.switch_to(self.sm.get_screen("login"))

    def switch_main(self):
        """
        Trigger ScreenManager to switch to the "main" screen.
        """

        self.client.debug("switching to the main screen")
        try:
            self.sm.get_screen("main")
        except:
            self.client.warning("failed to retrieve main screen, reinitializing")
            if not self.screens.get("main"):
                self.screens["main"] = MainScreenWithTopPanel(name="main", app=self)
            self.sm.add_widget(self.screens["main"])
        finally:
            self.sm.transition.direction = "left"
            self.sm.switch_to(self.sm.get_screen("main"))

    def build(self, client):
        """
        Builds graphical user interface.

        Positional arguments:
            client: backend.Client
                client instance connecting the View layer with the Controller layer (MVC pattern).

        Returns 
            kivy.uix.screenmanageR.MDScreenManager
        """
        
        self.client = client

        self.sm = WindowManager(transition=SlideTransition())
        # using monkey patching to extend properties of the client instance
        # to store theme information
        if not self.client.get('theme_style'):
            self.client['theme_style'] = "Dark"
        if not self.client.get('primary_palette'):
            self.client['primary_palette'] = "LightGreen"
        if not self.client.get('accent_palette'):
            self.client['accent_palette'] = "Teal"

        # setup theme properties
        self.theme_cls.theme_style = self.client['theme_style']
        self.theme_cls.primary_palette = self.client['primary_palette']
        self.theme_cls.accent_palette = self.client['accent_palette'] 
        self.theme_cls.accent_light_hue = "500" # default: 300
        self.theme_cls.accent_hue = "700" # default: 500
        self.theme_cls.accent_dark_hue = "900" # default: 700
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.8
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.custom_logo = 'data/dark.png'
        else:
            self.theme_cls.custom_logo = 'data/light.png'

        # initialize screen instances
        self.screens["login"] = LoginWindow(name="login", app=self)
        self.screens["main"] = MainScreenWithTopPanel(name="main", app=self)
        for screen in self.screens.values():
            # set logo
            screen.ids.logo.source = self.theme_cls.custom_logo
            self.sm.add_widget(screen)

        # begin with the "login" screen
        self.sm.switch_to(self.sm.get_screen("login"))
        return self.sm

    def on_pause(self):
        """
        [https://kivy.org/doc/stable-2.0.0/api-kivy.app.html]
        On tablets and phones, the user can switch at any moment to another application. 
        By default, your application will close and the App.on_stop() event will be fired.
        If you support Pause mode, when switching to another application, 
        your application will wait indefinitely until the user switches back to your application.
        If True is returned (default case), the application will sleep until the OS resumes our App.
        """

        # here, some data could be saved if necessary
        return True

    def on_resume(self):
        """
        [https://kivy.org/doc/stable-2.0.0/api-kivy.app.html]
        On tablets and phones, the user can switch at any moment to another application. 
        By default, your application will close and the App.on_stop() event will be fired.
        If you support Pause mode, when switching to another application, 
        your application will wait indefinitely until the user switches back to your application.
        When the app is resumed, App.on_resume() is called.
        """
        
        # here, some data could be replaced if necessary
        pass

    def switch_theme(self):
        """
        Experimental implementation of switcher between light and dark mode.
        """

        # update monkey patched properties of the client instance
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.custom_logo = 'data/light.png'
            self.client['theme_style'] = "Light"
            self.client['primary_palette'] = "Teal"
            self.client['accent_palette'] = "LightGreen"
        else:
            self.theme_cls.custom_logo = 'data/dark.png'
            self.client['theme_style'] = "Dark"
            self.client['primary_palette'] = "LightGreen"
            self.client['accent_palette'] = "Teal"
        # apply changes to the app theme
        self.theme_cls.theme_style = self.client['theme_style']
        self.theme_cls.primary_palette = self.client['primary_palette']
        self.theme_cls.accent_palette = self.client['accent_palette'] 
        # update logo for each screen instance
        for screen in self.screens.values():
            screen.ids.logo.source = self.theme_cls.custom_logo
