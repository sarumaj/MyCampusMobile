# -*- coding: utf-8 -*-

from typing import Callable
from kivymd.uix.dialog.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from threading import Thread
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
import random
import time
from typing import Any

class ProgressContent(MDBoxLayout):
    """
    Content of the progress dialog.
    """

    # numeric progress affecting the state of the progress bar
    prog_val = NumericProperty(0)
    # upper limit of the progress property
    total = NumericProperty(100)
    # indicates whether the coroutine has been already dispatched
    has_started = BooleanProperty(False)
    # Status message displayed below the progress bar
    status_msg = StringProperty('')
    # place holder for exception to be caught
    exception = ObjectProperty(None)

class ProgressPopup(MDDialog):
    """
    Dialog displaying progress bar and status message.
    """

    def __init__(self, **kwargs: dict[str,Any]):
        """
        Sets the content class explicitly to ProgressContent.

        Keyword arguments:
            **kwargs: dict[str,Any],
                Keyword arguments of the kivymd.uix.dialog.dialog.MDDialog class.
        """
        self.content_cls = ProgressContent()
        super().__init__(**kwargs)    

    @property
    def prog_val(self):
        """
        Getter for th content_class
        """
        return self.content_cls.prog_val

    @prog_val.setter
    def prog_val(self, __v):
        self.content_cls.prog_val = __v

    @property
    def status_msg(self):
        return self.content_cls.status_msg

    @status_msg.setter
    def status_msg(self, __v):
        self.content_cls.status_msg = __v

    @property
    def exception(self):
        return self.content_cls.exception

    @exception.setter
    def exception(self, __v):
        self.content_cls.exception = __v

    @property
    def has_started(self):
        return self.content_cls.has_started

    @has_started.setter
    def has_started(self, __v):
        self.content_cls.has_started = __v

    def run_worker(self, func:Callable, *args, **kwargs):
        self.content_cls.has_started = True
        Thread(target=func, args=args, kwargs=(kwargs if kwargs else None)).start()

    def on_dismiss(self):
        self.content_cls.has_started = False

    def schedule_auto_update(self, step:int, interval:float):
        def updater(self, step, interval):
            while True:
                new_val = self.content_cls.prog_val + random.randint(1, step)
                if new_val >= 100:
                    break
                self.content_cls.prog_val = new_val
                time.sleep(interval*random.randint(1, 5))
        Thread(target=updater, args=(self, step, interval)).start()