# -*- coding: utf-8 -*-

from kivy.lang import Builder
from pathlib import Path

# discover and read all kivy files
for kv in (Path(__file__).parent / 'kivy').glob('*.kv'):
    try:
        Builder.load_file(str(kv))
    except BaseException as ex:
        raise Exception(f"failed to parse {kv}", *ex.args)