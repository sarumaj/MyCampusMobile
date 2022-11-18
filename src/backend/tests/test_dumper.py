# -*- coding: utf-8 -*-

import tempfile
import unittest
from pathlib import Path

from backend.dumper import dump4mock


class Test:
    keys = []

    @classmethod
    def test_class_method(class_, idx):
        val = list(range(10))
        class_.keys.append(
            dump4mock(
                "val[%(c)d]@test(idx=%(c)d),test(idx=%(c)d)@test(idx=%(c)d)"
                % {"c": idx}
            )
        )
        return val[idx]

    def test_instance_method(self_, idx):
        val = list(range(10))
        self_.keys.append(
            dump4mock(
                "val[%(c)d]@test(idx=%(c)d),test(idx=%(c)d)@test(idx=%(c)d)"
                % {"c": idx}
            )
        )
        return val[idx]


class TestChild(Test):
    keys = []

    @classmethod
    def test_class_method_child(class_, idx):
        val = {i: i for i in range(10)}
        class_.keys.append(
            dump4mock(
                "val[%(c)d]@test(idx=%(c)d),test(idx=%(c)d)@test(idx=%(c)d)"
                % {"c": idx}
            )
        )
        return val[idx]

    def test_instance_method_child(self, idx):
        val = {i: i for i in range(10)}
        self.keys.append(
            dump4mock(
                "val.get(%(c)d)@test(idx=%(c)d),test(idx=%(c)d)@test(idx=%(c)d)"
                % {"c": idx}
            )
        )
        return val.get(idx)


class DumperTestCase(unittest.TestCase):
    def setUp(self):
        dump4mock.DUMP_CLASS = [Test, "TestChild"]
        self.restore, dump4mock.MOCK_DIR = dump4mock.MOCK_DIR, Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        dump4mock(["Test", "TestChild"])
        dump4mock.MOCK_DIR = self.restore

    def test_parent_class(self):
        Test.keys.clear()
        Test.test_class_method(2)
        Test().test_instance_method(3)
        keys = list(map(lambda x: str(x.name), Test.keys))
        self.assertEqual(
            True,
            "Test.test_class_method.val@test(idx=2),test(idx=2)@test(idx=2)#1.dump"
            in keys,
        )
        self.assertEqual(
            True,
            "Test.test_instance_method.val@test(idx=3),test(idx=3)@test(idx=3)#1.dump"
            in keys,
        )
        self.assertEqual(
            dump4mock[
                "Test.test_class_method.val@test(idx=2),test(idx=2)@test(idx=2)#1.dump"
            ],
            2,
        )
        self.assertEqual(
            dump4mock[
                "Test.test_instance_method.val@test(idx=3),test(idx=3)@test(idx=3)#1.dump"
            ],
            3,
        )

    def test_mro_from_within_child_class(self):
        TestChild.keys.clear()
        TestChild.test_class_method(2)
        TestChild().test_instance_method(3)
        TestChild.test_class_method_child(4)
        TestChild().test_instance_method_child(5)
        keys = list(map(lambda x: str(x.name), TestChild.keys))
        self.assertEqual(
            True,
            "Test.test_class_method.val"
            "@test(idx=2),test(idx=2)"
            "@test(idx=2)#1.dump" in keys,
        )
        self.assertEqual(
            True,
            "Test.test_instance_method.val"
            "@test(idx=3),test(idx=3)"
            "@test(idx=3)#1.dump" in keys,
        )
        self.assertEqual(
            dump4mock[
                "Test.test_class_method.val"
                "@test(idx=2),test(idx=2)"
                "@test(idx=2)#1.dump"
            ],
            2,
        )
        self.assertEqual(
            dump4mock[
                "Test.test_instance_method.val"
                "@test(idx=3),test(idx=3)"
                "@test(idx=3)#1.dump"
            ],
            3,
        )
        self.assertEqual(
            True,
            "TestChild.test_class_method_child.val"
            "@test(idx=4),test(idx=4)"
            "@test(idx=4)#1.dump" in keys,
        )
        self.assertEqual(
            True,
            "TestChild.test_instance_method_child.val.get"
            "@test(idx=5),test(idx=5)"
            "@test(idx=5)#1.dump" in keys,
        )
        self.assertEqual(
            dump4mock[
                "TestChild.test_class_method_child.val"
                "@test(idx=4),test(idx=4)"
                "@test(idx=4)#1.dump"
            ],
            4,
        )
        self.assertEqual(
            dump4mock[
                "TestChild.test_instance_method_child.val.get"
                "@test(idx=5),test(idx=5)"
                "@test(idx=5)#1.dump"
            ],
            5,
        )
