# -*- coding: utf-8 -*-

from kivy.lang import Builder
from pathlib import Path

for kv in (Path(__file__).parent / 'kivy').glob('*.kv'):
    Builder.load_file(str(kv))