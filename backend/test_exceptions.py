# -*- coding: utf-8 -*-

import sys
import unittest
from pathlib import Path

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

from .exceptions import ExceptionHandler, RequestFailed, SignInFailed, SignOutFailed

handler = ExceptionHandler(
    {
        SignInFailed: "SignInFailed has been raised",
        SignOutFailed: "SignOutFailed has been raised",
    },
    RequestFailed,
)

simple_handler = ExceptionHandler("something has been raised", RequestFailed)


class TestObject:
    @handler
    def raise_sign_in_exception(self):
        raise SignInFailed

    @handler
    def raise_sign_out_exception(self):
        raise SignOutFailed

    @handler
    def raise_unknown_exception_exception(self):
        raise Exception


class ExceptionsTestCase(unittest.TestCase):
    def setUp(self):
        self.test_object = TestObject()

    def test_handler(self):
        # match exception message by exception type #1
        with self.assertRaises(RequestFailed) as cm:
            self.test_object.raise_sign_in_exception()
        self.assertEqual(str(cm.exception.args[0]), "SignInFailed has been raised")

        # match exception message by exception type #2
        with self.assertRaises(RequestFailed) as cm:
            self.test_object.raise_sign_out_exception()
        self.assertEqual(str(cm.exception.args[0]), "SignOutFailed has been raised")

        # do not match exception message by exception type
        with self.assertRaises(RequestFailed) as cm:
            self.test_object.raise_unknown_exception_exception()
        self.assertEqual(str(cm.exception.args[0]), "unknown exception occured")

        # handle trivially
        with self.assertRaises(RequestFailed) as cm:
            simple_handler(self.test_object.raise_unknown_exception_exception)(self)
        self.assertEqual(str(cm.exception.args[0]), "something has been raised")


if __name__ == "__main__":
    unittest.main()
