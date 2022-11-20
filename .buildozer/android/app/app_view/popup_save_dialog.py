# -*- coding: utf-8 -*-

from typing import Any, Callable

from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.banner import MDBanner
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog

from .platform_specs import download_dir_path
from .platform_specs import open as dopen

Builder.load_string(
    r"""
#:kivy 2.1.0
#: import Path pathlib.Path

<SaveDialogContent>:
    orientation: "vertical"
    spacing: "20dp"
    padding: "20dp"
    size_hint_y: None
    adaptive_height: True

    FileChooserIconView:
        id: filechooser
        path: ""
        height: "500dp"
        size_hint_y: None
        dirselect: True
        on_selection: 
            text_input.text = self.selection[0] if self.selection and self.selection[0] and not Path(self.selection[0]).is_dir() else ''
            

    MDTextField:
        id: text_input
        multiline: False
        text: root.dialog.content_disposition
        width: self.width
        multiline: False
        font_size: '16sp'
        required: True
        helper_text: "Enter a file name"
        helper_text_mode: "on_error"
        adaptive_height: True

    MDRelativeLayout:
        size_hint: (1, None)
        height: "30dp"
        spacing: "40dp"
        padding: ("20dp", 0)
        adaptive_height: True

        MDRectangleFlatButton:
            text: "Cancel"
            padding: ("20dp", 0)
            pos_hint: {"left":1}
            text_size: self.size
            on_release: root.dialog.dismiss()

        MDRectangleFlatButton:
            text: "Save"
            padding: ("20dp", 0)
            pos_hint: {"right":1}
            text_size: self.size
            on_release: root.dialog.save(text_input.text, filechooser.path)

<SaveDialog>:
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


class SaveDialogContent(MDBoxLayout):
    """
    Content of the save dialog.
    """

    # reference to the poup instance
    dialog = ObjectProperty(None)

    def __init__(self, *, dialog: MDDialog, **kwargs: dict[str, Any]):
        """
        Create dialog body.

        Keyword arguments:
            dialog: kivymd.uix.banner.MDBanner,
                refeence to the implementing class.

            **kwargs: dict[str,Any],
                keyord arguments passed to the kivymd.uix.boxlayout.MDBoxLayout class.
        """

        self.dialog = dialog
        super().__init__(**kwargs)
        self.ids.filechooser.path = download_dir_path


class SaveDialog(MDDialog):
    """
    Dialog dispatching file chooser and saving downloaded content into the target location.
    """

    # content disposition describing the type of the downloaded content (MIME standard)
    content_disposition = StringProperty("")
    # function to be called to save the contents
    save_method = ObjectProperty(None)
    # reference to the banner of the implementing screen
    banner = ObjectProperty(None)

    def __init__(
        self,
        *,
        content_disposition: str,
        save_method: Callable,
        banner: MDBanner,
        **kwargs,
    ):
        """
        Class constructor.

        Keyword arguments:
            content_disposition: str,
                describes the type of the downloaded content (MIME standard).

            save_method: Callable,
                function to be called to save file contents.

            banner: kivymd.uix.dialog.MDBanner,
                reference to the banner of the implementing screen.
        """
        self.content_disposition = content_disposition
        self.save_method = save_method
        self.banner = banner
        self.content_cls = SaveDialogContent(dialog=self)
        return super().__init__(**kwargs)

    def save(self, file: str, path: str):
        """
        Wrapper used to execute the Callable save_method.

        Positional arguments:
            file: str,
                filename.

            path: str,
                file location (directory).
        """

        output = str(self.save_method(file, path))
        # dispatch notification
        self.banner.text = ["Download completed!", f'Saved to:\n"{output}".']
        self.banner.show()
        self.dismiss()
        # open file with default file handler specific for given type of file
        dopen(output)
