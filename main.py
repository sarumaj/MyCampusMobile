# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

from kivy.core.window import Window

os.environ["KIVY_IMAGE"] = "pil,sdl2"
Window.size = (720, 1440)
Window.minimum_height = 1000
Window.minimum_width = 600

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

if __name__ == "__main__" and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = ".".join(parent.parts[len(top.parts) :])

# trunk-ignore(flake8/E402)
from .backend import Client

# trunk-ignore(flake8/E402)
from .frontend import MobileApp, app_dir_path

CLIENT = Client(
    "",
    "",
    max_len=100,
    max_age=60**2,
    filepath=__file__,
    verbose=True,
    destination=str(Path(app_dir_path) / "cache.dat"),
)

if __name__ == "__main__":
    app = MobileApp(CLIENT)
    app.run()
