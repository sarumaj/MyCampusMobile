# -*- coding: utf-8 -*-

from kivy.properties import (
    ObjectProperty,
    StringProperty,
)
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from typing import Callable
from kivymd.uix.banner import MDBanner
from typing import Any

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

from .platform_specs import open as dopen
from .platform_specs import download_dir_path

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

    def __init__(self, *, dialog:MDDialog, **kwargs:dict[str,Any]):
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
    content_disposition = StringProperty('')
    # function to be called to save the contents
    save_method = ObjectProperty(None)
    # reference to the banner of the implementing screen
    banner = ObjectProperty(None)

    def __init__(
        self, *,
        content_disposition:str,
        save_method:Callable,
        banner:MDBanner,
        **kwargs
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

    def save(self, file:str, path:str):
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
        self.banner.text = [
            "Download completed!",
            f'Saved to:\n"{output}".'
        ]
        self.banner.show()
        self.dismiss()
        # open file with default file handler specific for given type of file
        dopen(output)