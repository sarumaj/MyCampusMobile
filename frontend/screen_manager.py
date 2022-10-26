# -*- coding: utf-8 -*-

from kivymd.uix.screenmanager import MDScreenManager
from kivy.properties import (StringProperty, NumericProperty)

class WindowManager(MDScreenManager):
    selected_course_id = NumericProperty(0) 
    selected_course_name = StringProperty('')

