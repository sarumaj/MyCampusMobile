# -*- coding: utf-8 -*-

from inspect import trace
import traceback

# preamble to prevent unknown 

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

from .logger import Logger

class SignInFailed(Exception):
    """
    Exception to be raised whenever the SAML authentication request fails.
    """

class SignOutFailed(Exception):
    """
    Exception to be raised whenever the sign-out request fails.
    """

class RequestFailed(Exception):
    pass

class ExceptionHandler:
    """
    Decorator used to wrap class methods to handle inner exceptions gracefully.
    """
    
    def __init__(self, msg:str, ex:Exception):
        self.msg = msg
        self.ex = ex

    def __call__(self, func):
        def inner(instance, *args, **kwargs):
            try:
                return func(instance, *args, **kwargs)
            except:
                # catch exception
                try:
                    # raise custom exception
                    raise self.ex(self.msg)
                except BaseException as ex:
                    # catch again
                    if isinstance(instance, Logger):
                        # log full trace
                        instance.error(traceback.format_exc())
                    # re-raise with shortened trace
                    raise ex from None
        return inner
