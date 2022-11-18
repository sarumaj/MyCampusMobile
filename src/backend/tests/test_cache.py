# -*- coding: utf-8 -*-

import tempfile
import time
import unittest

from backend.cache import Cache


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        self.cache = Cache(
            filepath=tempfile.gettempdir(),
            verbose=False,
            emit=False,
            max_len=100,
            max_age=30 * 60**2,
        )

    def test_run(self):
        def test_storing_primitive_type(self):
            self.cache["integer"] = 1
            self.assertEqual(self.cache.get("integer"), 1, "failed to store integer")

        def test_storing_complex_type(self):
            self.cache["dict"] = dict()
            self.cache.get("dict", {})["integer"] = 1
            self.assertEqual(
                self.cache.get("dict"), {"integer": 1}, "failed to store dict object"
            )
            with self.assertRaises(KeyError):
                self.cache["dict2"]["integer"] = 1
            self.assertEqual(self.cache.get("dict2"), None, "expected failure")
            self.cache.get("dict3", {})["integer"] = 1
            self.assertEqual(self.cache.get("dict3"), None, "expected failure")

        def test_extending_life_time(self):
            future = time.time() + 1_000_000
            self.cache.__setitem__("immortal", 1, future)
            self.assertEqual(
                self.cache.get("immortal"), 1, "failed to store immortal object"
            )
            self.assertEqual(
                next(
                    filter(
                        lambda x: x[0] == "immortal", self.cache.items_with_timestamp()
                    )
                )[-1][-1],
                future,
                "failed to store immortal object",
            )

        def test_prolongation(self):
            offset = 1_000_000
            self.cache["to_prolongate"] = 1
            now = time.time()
            self.cache.prolongate("to_prolongate", offset)
            self.assertEqual(
                self.cache.get("to_prolongate"), 1, "failed to store object"
            )
            self.assertEqual(
                int(
                    next(
                        filter(
                            lambda x: x[0] == "to_prolongate",
                            self.cache.items_with_timestamp(),
                        )
                    )[-1][-1]
                    - now
                ),
                offset,
                "failed to prolongate stored object",
            )

        def test_removal(self):
            self.cache["temporary"] = 1
            self.cache.pop("temporary")
            with self.assertRaises(KeyError):
                self.cache["temporary"]
            self.assertEqual(self.cache.get("temporary"), None, "expected failure")

        test_storing_primitive_type(self)
        test_storing_complex_type(self)
        test_extending_life_time(self)
        test_prolongation(self)
        test_removal(self)
