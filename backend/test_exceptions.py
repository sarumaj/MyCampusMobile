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

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .exceptions import *

handler = ExceptionHandler({
    SignInFailed: "SignInFailed has been raised",
    SignOutFailed: "SignOutFailed has been raised",
}, RequestFailed)

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
        self.assertEqual(str(cm.exception), 'SignInFailed has been raised')

        # match exception message by exception type #2
        with self.assertRaises(RequestFailed) as cm:
            self.test_object.raise_sign_out_exception()
        self.assertEqual(str(cm.exception), 'SignOutFailed has been raised')

        # do not match exception message by exception type
        with self.assertRaises(RequestFailed) as cm:
            self.test_object.raise_unknown_exception_exception()
        self.assertEqual(str(cm.exception), 'unknown exception occured')
        
        # handle trivially
        with self.assertRaises(RequestFailed) as cm:
            simple_handler(self.test_object.raise_unknown_exception_exception)(self)
        self.assertEqual(str(cm.exception), 'something has been raised')

if __name__ == "__main__":
    unittest.main()