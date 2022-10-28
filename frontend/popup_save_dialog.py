# -*- coding: utf-8 -*-

from kivy.uix.popup import Popup
from kivy.properties import (
    ObjectProperty,
    StringProperty,
)
from kivymd.uix.dialog.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

from popup_notifier import Notifier
from platform import open


class SaveDialogContent(MDBoxLayout):
    master = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        self.master = kwargs.pop('master')
        super().__init__(*args, **kwargs)

class SaveDialog(MDDialog):
    content_disposition = StringProperty('')
    save_method = ObjectProperty(None)
    banner = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.content_disposition = kwargs.pop('content_disposition')
        self.save_method = kwargs.pop('save_method')
        self.banner = kwargs.pop('banner')
        self.content_cls = SaveDialogContent(master=self)
        return super().__init__(**kwargs)

    def save(self, file:str, path:str):
        output = str(self.save_method(file, path))
        self.banner.text = [
            "Download completed!",
            f'Saved to:\n"{output}".'
        ]
        self.banner.show()
        self.dismiss()
        open(output)