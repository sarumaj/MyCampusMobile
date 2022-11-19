# -*- coding: utf-8 -*-

import os
from pathlib import Path

import certifi

from backend import Client
from frontend import MobileApp, app_dir_path

os.environ["KIVY_IMAGE"] = "pil,sdl2"
os.environ["SSL_CERT_FILE"] = certifi.where()

CLIENT = Client(
    "",
    "",
    max_len=100,
    max_age=60**2,
    filepath=__file__,
    verbose=True,
    destination=str(Path(app_dir_path) / ".cache.dat"),
)


def main():
    app = MobileApp(CLIENT)
    app.run()


if __name__ == "__main__":
    from kivy.utils import platform

    if platform != "android":
        from kivy.core.window import Window

        Window.size = (720, 1440)
        Window.minimum_height = 1000
        Window.minimum_width = 600
    main()
