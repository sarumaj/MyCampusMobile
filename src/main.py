# -*- coding: utf-8 -*-

import os
from pathlib import Path

import certifi
from kivy.core.window import Window

os.environ["KIVY_IMAGE"] = "pil,sdl2"
os.environ["SSL_CERT_FILE"] = certifi.where()
Window.size = (720, 1440)
Window.minimum_height = 1000
Window.minimum_width = 600

# trunk-ignore(flake8/E402)
from backend import Client

# trunk-ignore(flake8/E402)
from frontend import MobileApp, app_dir_path

CLIENT = Client(
    "",
    "",
    max_len=100,
    max_age=60**2,
    filepath=__file__,
    verbose=True,
    destination=str(Path(app_dir_path) / ".cache.dat"),
)

if __name__ == "__main__":
    app = MobileApp(CLIENT)
    app.run()
