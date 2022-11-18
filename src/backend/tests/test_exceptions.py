# -*- coding: utf-8 -*-

import unittest

from backend.exceptions import (
    ExceptionHandler,
    RequestFailed,
    SignInFailed,
    SignOutFailed,
)

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
