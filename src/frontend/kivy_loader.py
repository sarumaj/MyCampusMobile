# -*- coding: utf-8 -*-

from pathlib import Path

from kivy.lang import Builder

# discover and read all kivy files
for kv in (Path(__file__).parent / "kivy").glob("*.kv"):
    try:
        Builder.load_file(str(kv))
    except BaseException as ex:
        raise Exception(f"failed to parse {kv}", *ex.args)
