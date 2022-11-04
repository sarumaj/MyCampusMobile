# -*- coding: utf-8 -*-

import traceback
from typing import (Union, Callable, Any)

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
    
    def __init__(self, message:Union[dict[Exception,str],str], ex:Exception):
        """
        Used to parametrize the caller.

        Positional arguments:
            message: Union[dict[Exception,str],str],
                exception message or a mapping of exception messages matching expected exceptions.

            ex: Exception,
                exception to be raised with the custom message.
        """

        self.msg = message
        self.ex = ex

    def __call__(self, func:Callable):
        def inner(instance:object, *args:tuple[Any], **kwargs:dict[str,Any]):
            try:
                return func(instance, *args, **kwargs)
            except BaseException as ex:
                # catch exception
                try:
                    # raise custom exception
                    if isinstance(self.msg, dict):
                        for k, v in self.msg.items():
                            if isinstance(ex, k):
                                raise self.ex(v)
                        raise self.ex("unknown exception occured")
                    else:
                        raise self.ex(str(self.msg))
                except BaseException as ex:
                    # catch again
                    if isinstance(instance, Logger):
                        # log full trace
                        instance.error(traceback.format_exc())
                    # re-raise with shortened trace
                    raise ex from None
        return inner
