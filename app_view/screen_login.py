# -*- coding: utf-8 -*-

import random
from typing import Any

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors.focus import FocusBehavior
from kivymd.app import MDApp
from kivymd.uix.button.button import MDRectangleFlatIconButton
from kivymd.uix.dialog.dialog import MDDialog
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield.textfield import MDTextField

from .popup_progress import ProgressPopup

Builder.load_string(
    r"""
#:kivy 2.1.0

<CredentialInput>:
    multiline: False
    font_size: '20sp'
    required: True

<LoginWindow>:
    name: "login"

    MDBanner:
        id: banner
        text: []
        over_widget: main_layout
        vertical_pad: 0
        type: "two-line"
        right_action: ["CLOSE", lambda bound_instance: (self.hide(), setattr(theme_switcher, 'disabled', False))]

    AnchorLayout:
        anchor_x: "right"
        anchor_y: "top"

        MDIconButton:
            id: theme_switcher
            icon: "theme-light-dark"
            theme_icon_color: "Custom"
            icon_color: app.theme_cls.primary_color
            on_release:
                app.switch_theme()
            
    BoxLayout:
        id: main_layout
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(10)

        Label:
            size_hint:(1,.1)

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
                adaptive_size: True
                size_hint: (None, None)

                FitImage:
                    id: logo
                    #source: app.theme_cls.custom_logo 
                    size: (dp(200), dp(200))
                    size_hint: (None, None)
                    text_size: self.size
                    halign: 'right'
                    valign: 'middle'

                MDLabel:
                    id: title
                    text: "INTERNATIONAL\nUNIVERSITY\nOF APPLIED SCIENCES"
                    font_size: '32sp'
                    text_size: self.size
                    height: self.texture_size[1]
                    width: dp(250)
                    size_hint: (None, None)
                    halign: 'left'
                    valign: 'top'
                    theme_text_color: "Custom"
                    text_color: app.theme_cls.opposite_bg_normal

            MDLabel:
                text: "MyCampus Mobile"
                font_size: '36sp'
                text_color: app.theme_cls.primary_dark
                theme_text_color: "Custom"
                height: self.texture_size[1]
                text_size: self.size
                size_hint:(1, None)
                halign: 'center'
                valign: 'bottom'

        Label:
            size_hint:(1,.3)

        CredentialInput:
            id: username
            screen: root
            hint_text: "Username"
            pos_hint:{"center_x":.5}
            size: (password.width, dp(40))
            size_hint:(None,None)
            on_text_validate: password.focus = True
            helper_text: "Username is required!"
            helper_text_mode: "on_error"
            icon_left: "account"

        ClickableTextFieldRound:
            size_hint: (None, None)
            pos_hint:{"center_x":.5}
            size: password.size

            CredentialInput:
                id: password
                screen: root
                hint_text: "Password"
                password: True
                size_hint:(None,None)
                size: (logo.width+title.width, dp(40))
                on_text_validate: sign_in_btn.focus = True
                helper_text: "Password is required!"
                helper_text_mode: "on_error"
                icon_left: "key-variant"

            MDIconButton:
                icon: "eye-off"
                pos_hint: {"center_y": .5}
                pos: password.width - self.width + dp(8), 0
                theme_text_color: "Hint"
                on_release:
                    self.icon = "eye" if self.icon == "eye-off" else "eye-off"
                    password.password = not password.password

        FocusableButton:
            id: sign_in_btn
            icon: "login-variant"
            text: "Sign in"
            font_size: '20sp'
            on_release: 
                self.disabled = True
                root.login()
                self.disabled = False
            pos_hint:{"center_x":.5}
            size_hint:(None,None)
            text_size: self.size
            theme_icon_color: "Custom"
            icon_color: app.theme_cls.primary_color
            theme_text_color: "Custom"
            text_color: app.theme_cls.primary_color
            line_color: app.theme_cls.primary_color

        Label:
            size_hint:(1,.2)
"""
)

###############
#             #
# definitions #
#             #
###############


class FocusableButton(MDRectangleFlatIconButton, FocusBehavior):
    """
    Custom button class extending default button behavior.
    """


class ClickableTextFieldRound(MDRelativeLayout):
    """
    Custom widget to tweak the text input field.
    """

    # reference to the content of the text input field
    text = StringProperty()
    # reference to the hint text of the text input field
    hint_text = StringProperty()


class CredentialInput(MDTextField):
    """
    Customized text input field.
    """

    # reference to the screen utilizing the widget.
    screen = ObjectProperty(None)

    def keyboard_on_key_down(self, keyboard, keycode, text, modifiers):
        """
        Handling key_down event.

        Positional arguments:
            parameters adhering to the specification of kivy.uix.vkeyboard

        """
        if keycode[0] == 9 and hasattr(self.screen, "toggle_focus"):  # tab
            self.screen.toggle_focus()
        return super().keyboard_on_key_down(keyboard, keycode, text, modifiers)


class LoginWindow(MDScreen):
    """
    Login screen extending kivymd.uix.screen.MDScreen.
    """

    # observeable app reference
    app = ObjectProperty(None)

    def __init__(self, *, app: MDApp, **kwargs: dict[str, Any]):
        """
        Create login window.

        Keyword arguments:
            app: MDApp
                observable reference of the MDApp instance.

            **kwargs: dict[str,Any]
                keyword arguments supported by the parent class MDScreen.
        """

        self.app = app
        # setup keyboard listener to handle key_down events
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        super().__init__(**kwargs)

        def experimental_warning(*args):
            self.ids.theme_switcher.disabled = True
            Clock.schedule_once(
                lambda dt: (
                    self.ids.banner.hide(),
                    setattr(self.ids.theme_switcher, "disabled", False),
                ),
                self.ids.banner.opening_time + self.ids.banner.closing_time + 5,
            )
            self.ids.banner.text = [
                "Warning!",
                "The LIGHT theme is provided as is. "
                "It is recommened to use the DARK theme instead!",
            ]
            self.ids.banner.show()

        self.ids.theme_switcher.bind(on_release=experimental_warning)

    @property
    def client(self):
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
                arguments forwarded to kivymd.uix.screen.MDScreen.on_enter method.
        """

        # get username from cache
        self.ids.username.text = self.app.client.get("username", "")
        # set up initila focus
        if self.ids.username.text:
            self.ids.password.focus = True
        else:
            self.ids.username.focus = True
        return super().on_enter(*args)

    def _keyboard_closed(self):
        """
        Called when user closes virtual keyboard instance.
        """

        pass

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Handling key_down event.

        Positional arguments:
            parameters adhering to the specification of kivy.uix.vkeyboard

        """

        if keycode[0] == 13 and self.ids.sign_in_btn.focus:  # enter
            self.ids.sign_in_btn.trigger_action()
        if keycode[0] == 9:  # tab
            self.toogle_focus()
        return True

    def toogle_focus(self):
        """
        Toggle focus from one widget to another.
        """

        if self.ids.username.focus:
            self.ids.password.focus = True
        elif self.ids.password.focus:
            self.ids.sign_in_btn.focus = True
        else:
            self.ids.username.focus = True

    def login(self):
        """
        Performs sign-in and switches to the main screen.
        """

        # pass credentials to the client instance
        self.app.client.username = self.ids.username.text.strip()
        self.app.client.password = self.ids.password.text.strip()
        # dispatch progress popup
        popup = ProgressPopup(title="Signing in...")
        popup.open()

        def perform_login(self, popup: MDDialog):
            """
            Worker perfoming sign-in actions and updating the state of the progress popup.

            Positional arguments:
                popup: kivymd.uix.dialog.dialog.MDDialog
                    custom popup displaying progress of the sign-in procedure.
            """
            try:
                # perform sign-in actions
                popup.status_msg = "Establishing connection..."
                SAMLrequest = self.client.get_saml_request()
                popup.prog_val = random.randint(1, 50)

                popup.status_msg = "Exchanging handshake.."
                SAMLresponse = self.client.get_saml_response(SAMLrequest)
                popup.prog_val = random.randint(1, 50)

                popup.status_msg = "Signing in..."
                self.client.submit_saml_response(SAMLresponse)

                # finished
                popup.prog_val = 100

            except BaseException as ex:
                # pass exception to disrupt the watch-dog
                popup.exception = ex

            finally:
                popup.dismiss()

        # run as child thread in background
        popup.run_worker(perform_login, self, popup)

        def perfom_switch(dt: int):
            """
            Watch-dog observing the state of the progress popup.

            Positional arguments:
                dt: int
                    interval in seconds denoting the lookup frequency.
            """

            if popup.has_started and popup.exception is None:
                # child thread still running...
                Clock.schedule_once(perfom_switch, dt)
            else:
                # child thread has finished
                # clear password input field
                self.ids.password.text = ""
                if isinstance(popup.exception, Exception):
                    # display warning in a banner
                    self.ids.banner.text = [
                        popup.exception.args[0][:1].upper()
                        + popup.exception.args[0][1:]
                        + ".",
                        "Check your credentials.",
                    ]
                    self.ids.banner.show()
                else:
                    # perform switch to the main screen
                    self.app.switch_main()

        # dispatch watch-dog
        perfom_switch(1)

    def __del__(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None
