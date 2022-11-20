# -*- coding: utf-8 -*-

import random
import time
from threading import Thread
from typing import Any, Callable

from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog.dialog import MDDialog

Builder.load_string(
    r"""
#:kivy 2.1.0

<ProgressContent>:
    orientation: "vertical"
    spacing: "20dp"
    padding: "20dp"
    size_hint_y: None
    adaptive_height: True

    MDProgressBar:
        pos_hint: {"center_x" : 0.5}
        size_hint: (1, None)
        height: "5dp"
        value: root.prog_val
        max: root.total

    MDLabel:
        id: lbl
        pos_hint: {"center_x" : 0.5}
        halign: "center"
        text: "{0} ({1:.0%})".format(root.status_msg, root.prog_val/root.total) if root.has_started else ""

<ProgressPopup>:
    size_hint: (.8, None)
    auto_dismiss: False
    type: "custom"
    radius: (20, 7, 20, 7)
"""
)

###############
#             #
# definitions #
#             #
###############


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
    status_msg = StringProperty("")
    # place holder for exception to be caught
    exception = ObjectProperty(None)


class ProgressPopup(MDDialog):
    """
    Dialog displaying progress bar and status message.
    """

    def __init__(self, **kwargs: dict[str, Any]):
        """
        Sets the content class explicitly to ProgressContent.

        Keyword arguments:
            **kwargs: dict[str,Any],
                Keyword arguments of the kivymd.uix.dialog.dialog.MDDialog class.
        """
        self.content_cls = ProgressContent()
        super().__init__(**kwargs)

    @property
    def prog_val(self) -> int:
        """
        Access point to the current value of the progress bar.

        Returns:
            int
        """

        return self.content_cls.prog_val

    @prog_val.setter
    def prog_val(self, __v: int):
        """
        Access point (setter) for the current value of the progress bar.

        Positional arguments:
            int
        """

        self.content_cls.prog_val = __v

    @property
    def total(self) -> int:
        """
        Access point to the maximum value of the progress bar.

        Returns:
            int
        """

        return self.content_cls.total

    @total.setter
    def total(self, __v: int):
        """
        Access point (setter) for the maximum value of the progress bar.

        Positional arguments:
            int
        """

        self.content_cls.total = __v

    @property
    def status_msg(self) -> str:
        """
        Access point to the status message.

        Returns:
            str
        """

        return self.content_cls.status_msg

    @status_msg.setter
    def status_msg(self, __v: str):
        """
        Access point (setter) for the status message.

        Positional arguments:
            str
        """

        self.content_cls.status_msg = __v

    @property
    def exception(self) -> Exception:
        """
        Access point to the internal exception object.

        Returns:
            Exception
        """

        return self.content_cls.exception

    @exception.setter
    def exception(self, __v: Exception):
        """
        Access point (setter) for the internal exception object.

        Positional arguments:
            Exception
        """

        self.content_cls.exception = __v

    @property
    def has_started(self) -> bool:
        """
        Access point to the "has_started" of the content class.

        Returns:
            bool
        """

        return self.content_cls.has_started

    @has_started.setter
    def has_started(self, __v: bool):
        """
        Access point (setter) for the "has_started" of the content class.

        Positional arguments:
            bool
        """

        self.content_cls.has_started = __v

    def run_worker(self, func: Callable, *args: tuple[Any], **kwargs: dict[str, Any]):
        """
        Dispatches a callable as a non-daemonic thread.

        Positional arguments:
            func: Callable,
                function to be executed in the thread.

            *args: tuple[Any],
                positional arguments passed to the callable function.

            **kwargs: dcit[str,Any],
                keyword arguments passed to the callable function.
        """

        self.has_started = True
        Thread(target=func, args=args, kwargs=(kwargs if kwargs else None)).start()

    def on_dismiss(self):
        """
        Called when the dialog is supposed to disappear.
        """

        self.has_started = False

    def schedule_auto_update(self, step: int, interval: float):
        """
        Method used to mock the update behavior of the progress bar.
        It updates the progress bar value by a random value between 1 and x
        every y seconds.

        Positional arguments:
            step: int,
                upper range boundary for the update value.

            interval: int,
                the update interval which will be multiplied with the random value between 1 and 5.
        """

        def updater(self, step: int, interval: float):
            """
            Inner function to be called in a dedicated thread.

            Positional arguments:
                same as for the outer method.
            """

            while True:
                new_val = self.prog_val + random.randint(1, step)
                if new_val >= self.total:
                    # progress is completed
                    break
                self.prog_val = new_val
                # wait before next update
                time.sleep(interval * random.randint(1, 5))

        # dispatch updater
        Thread(target=updater, args=(self, step, interval)).start()
