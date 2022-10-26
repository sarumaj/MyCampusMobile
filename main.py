# -*- coding: utf-8 -*-

from kivy.app import runTouchApp
from kivy.core.window import Window

Window.size = (720, 1440)
Window.minimum_height = 1000
Window.minimum_width = 600

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .frontend import (MobileApp, app_dir_path)
from .backend import Client

CLIENT = Client(
    '', '', max_len=100, max_age=60**2, 
    filepath=__file__, verbose=True, 
    destination=str(Path(app_dir_path) / "memory.dat")
)

if __name__ == '__main__':
    app = MobileApp()
    runTouchApp(app.build(CLIENT))