# -*- coding: utf-8 -*-

import unittest
import tempfile

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path
import time

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .cache import Cache

class CacheTestCase(unittest.TestCase):
    def setUp(self):
        self.cache = Cache(
            filepath=tempfile.gettempdir(), 
            verbose=True, 
            max_len=100, 
            max_age=30*60**2
        )

    def test_run(self):
        def test_storing_primitive_type(self):
            self.cache['integer'] = 1
            self.assertEqual(self.cache.get('integer'), 1, "failed to store integer")

        def test_storing_complex_type(self):
            self.cache['dict'] = dict()
            self.cache.get('dict', {})['integer'] = 1
            self.assertEqual(self.cache.get('dict'), {'integer':1}, "failed to store dict object")
            self.cache['dict2']['integer'] = 1
            self.assertEqual(self.cache.get('dict2'), {'integer':1}, "failed to store dict object")
            self.cache.get('dict3', {})['integer'] = 1
            self.assertEqual(self.cache.get('dict3'), {'integer':1}, "failed to store dict object")

        def test_extending_life_time(self):
            future = time.time() + 1_000_000
            self.cache.__setitem__('immortal', 1, future)
            self.assertEqual(self.cache.get('immortal'), 1, "failed to store immortal object")
            self.assertEqual(
                next(
                    filter(
                        lambda x: x[0] == 'immortal', 
                        self.cache.items_with_timestamp()
                    )
                )[-1][-1], 
                future, 
                "failed to store immortal object"
            )

        test_storing_primitive_type(self)
        test_storing_complex_type(self)
        test_extending_life_time(self)

if __name__ == "__main__":
    unittest.main()