# -*- coding: utf-8 -*-

from kivymd.app import MDApp
from kivy.uix.screenmanager import SlideTransition
from kivy.properties import (DictProperty, ObjectProperty)
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
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .screen_manager import WindowManager
#from .screen_login import LoginWindow
#from .screen_main import MainScreenWithTopPanel
from .platform_specs import app_dir_path

# dummies
class LoginWindow:
    pass

class MainScreenWithTopPanel:
    pass

##############
#            #
# definition #
#            #
##############

class MobileApp(MDApp):
    title = "MyCampus Mobile"
    icon = "data/dark.png"

    # stattic obervable storage for initialized screens (prevents unwanted garbage collection)
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
        try:
            self.sm.get_screen("main")
        except:
            if not self.screens.get("main"):
                self.screens["main"] = MainScreenWithTopPanel(name="main", app=self)
            self.sm.add_widget(self.screens["main"])
        finally:
            self.sm.transition.direction = "left"
            self.sm.switch_to(self.sm.get_screen("main"))

    def build(self, client):
        self.client = client

        self.sm = WindowManager(transition=SlideTransition())
        if not self.client.get('theme_style'):
            self.client['theme_style'] = "Dark"
        if not self.client.get('primary_palette'):
            self.client['primary_palette'] = "LightGreen"
        if not self.client.get('accent_palette'):
            self.client['accent_palette'] = "Teal"

        self.theme_cls.theme_style = self.client['theme_style']
        self.theme_cls.primary_palette = self.client['primary_palette']
        self.theme_cls.accent_palette = self.client['accent_palette'] 
        self.theme_cls.accent_light_hue = "500"
        self.theme_cls.accent_hue = "700"
        self.theme_cls.accent_dark_hue = "900"
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.8
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.custom_logo = 'data/dark.png'
        else:
            self.theme_cls.custom_logo = 'data/light.png'

        self.screens["login"] = LoginWindow(name="login", app=self)
        self.sm.add_widget(self.screens["login"])
        self.screens["main"] = MainScreenWithTopPanel(name="main", app=self)
        self.sm.add_widget(self.screens["main"])
        self.sm.get_screen("login").ids.logo.source = self.theme_cls.custom_logo
        self.sm.get_screen("main").ids.logo.source = self.theme_cls.custom_logo

        self.sm.switch_to(self.sm.get_screen("login"))
        return self.sm

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def switch_theme(self):
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
        self.theme_cls.theme_style = self.client['theme_style']
        self.theme_cls.primary_palette = self.client['primary_palette']
        self.theme_cls.accent_palette = self.client['accent_palette'] 
        self.sm.get_screen("login").ids.logo.source = self.theme_cls.custom_logo
        self.sm.get_screen("main").ids.logo.source = self.theme_cls.custom_logo


