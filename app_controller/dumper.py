# -*- coding: utf-8 -*-

import hashlib
import os
import pickle
import re
from inspect import getmembers, getmro, isfunction, ismethod, stack
from pathlib import Path
from typing import Any, Union


class __dump4mockMeta__(type):
    """
    Meta class making the target class subscriptable.
    """

    def __init__(self, *args, **kwargs):
        self._dump_class = []
        self._mock_dir = Path(__file__).parents[1] / "app_data" / "mock"

    # enable/disable globally for selected class instances
    @property
    def DUMP_CLASS(self):
        return self._dump_class

    @DUMP_CLASS.setter
    def DUMP_CLASS(self, value):
        def set(value):
            if isinstance(value, type):
                self._dump_class.append(value.__name__)
            else:
                self._dump_class.append(str(value))

        if isinstance(value, (tuple, list)):
            for v in value:
                set(v)
        else:
            set(value)

    # location for dumped files
    @property
    def MOCK_DIR(self):
        return self._mock_dir

    @MOCK_DIR.setter
    def MOCK_DIR(self, value):
        if isinstance(value, Path):
            self._mock_dir = value
        else:
            self._mock_dir = Path(str(value))

    # implements read behavior
    def __getitem__(cls, x: Union[str, Path]):
        if hasattr(cls, "__read__") and isinstance(x, (str, Path)):
            return cls.__read__(x)
        raise KeyError(x)


class dump4mock(metaclass=__dump4mockMeta__):
    """
    Internal tool to dump any Python object to local drive.
    It can be used as function or subscriptable object.
    Should be used only in the namespace of a class method.

    To enable the dump behavior, pass class obejct(s) to:
        dump4mock.DUMP_CLASS = class
    or:
        dump4mock.DUMP_CLASS = [class1, class2, ...]

    To clean dumped contents from local storage:
        dump4mock([class1, ...])

    Usage:
        Dump:
            path = dump4mock("variable.x") -> dump the value of the attribute "x" of the object "variable"
            path = dump4mock("class.method('arg1')") -> dump the return value of the class method for the argument 'arg1'
            path = dump4mock("class.method('arg1')@args=arg1@date=20221112)") -> use custom annotations
        Retrieve:
            stored_object = dump4mock[path]
    """

    def __new__(
        cls, fname: Union[str, Path], overwrite: bool = False, *args, **kwargs
    ) -> Any:
        """
        Overwrites memory allocator for the class.
        It prevents the class from creating own class instance and
        lets it be used as a mere function object.

        Positional arguments:
            fname, Union[str, Path, tuple[str]],
                file name, object identifier in the local namespace or list of classes
                for which the dumped files should be removed.

            overwrite: bool,
                if True, the dump file will be overwritten.

        Keyword arguments:
            context: int, default is 1,
                frame context level (namespace order number in the callers' stack).
        """

        if isinstance(fname, (list, tuple)):
            return dump4mock.__clear__(fname)
        elif (
            isinstance(fname, Path)
            and fname.exists()
            or len(fname) < os.pathconf(os.sep, "PC_NAME_MAX")
            and len(os.path.join(*map(str, [cls.MOCK_DIR, fname])))
            < os.pathconf(os.sep, "PC_PATH_MAX")
            and (
                dump4mock.MOCK_DIR
                / (str(fname).endswith(".dump") and fname or f"{fname}.dump")
            ).exists()
        ):
            return dump4mock.__read__(fname)
        else:
            return dump4mock.__dump__(str(fname), overwrite, context=2)

    @classmethod
    def __dump__(cls, key: str, overwrite: bool = False, *, context: int = 1) -> Path:
        """
        Dumps Python object into local drive.
        Object is identified by the key within the local namespace of given frame.

        Positional arguments:
            key: str,
                examples:
                     - result.text
                     - result[1]
                     - result.get(0, None)

            overwrite: bool,
                if True, the dump file will be overwritten.

        Keyword arguments:
            context: int, default is 1,
                frame context level (namespace order number in the callers' stack).
        """

        frames = stack()
        # method's frame (local namespace)
        frame_locals = frames[context][0].f_locals

        # regular expressions
        subscription = re.compile(r"(\(.*?\)|\[.+?\])(?=@)", re.DOTALL | re.MULTILINE)
        comment = re.compile(r"@(.*)$", re.DOTALL | re.MULTILINE)

        # template for the file name and keyword mapping for formatting
        tmpl, kwargs = "{class}.{method}.{key}#{cnt}.dump", {
            "class": frame_locals.get("self")
            and frame_locals["self"].__class__.__name__
            or frame_locals.get("cls")
            and frame_locals["cls"].__name__
            or "root",
            "method": frames[context].function,
            "cnt": 1,
            # simplify key in order to prevent violation of allowed filename charset
            "key": subscription.sub("", str(key), 1),
        }

        # apply method resolution order
        def apply_mro(cls):
            # apply MRO on class level and not instance level
            for cls_object in getmro(cls):
                # retrieve methods (for class level identified as function objects)
                for name, _ in getmembers(
                    cls_object, predicate=lambda o: isfunction(o) or ismethod(o)
                ):
                    # method found somewhere else in the MRO
                    if name == kwargs["method"]:
                        kwargs["class"] = cls_object.__name__

        if frame_locals.get("self"):
            apply_mro(frame_locals.get("self").__class__)
        elif frame_locals.get("cls"):
            apply_mro(frame_locals.get("cls"))
        else:
            for value in frame_locals.values():
                if isinstance(value, type):
                    apply_mro(value)
                elif isinstance(value, object):
                    apply_mro(value.__class__)

        target = cls.MOCK_DIR / tmpl.format(**kwargs)
        # strip annotations
        base = comment.sub("", subscription.sub("", str(key)))
        # retrieve content from the method's namespace
        content = frame_locals.get(base.split(".")[0])

        # if content is an object with attribute access chain
        # retrieve its final attribute in chain
        if len(base.split(".")) > 1:
            for attr in base.split(".")[1:]:
                # in the case attr is not present, content = content
                content = getattr(content, attr, content)

        # in the case the key descripes an access method or subscription
        # perform it to retrieve content
        if subscription.search(str(key)):
            match = subscription.search(str(key)).group(1)
            if (
                match.startswith("(")
                and match.endswith(")")
                and hasattr(content, "__call__")
            ):
                content = eval("content.__call__(%s)" % match.strip("()"), {}, locals())
            elif (
                match.startswith("[")
                and match.endswith("]")
                and hasattr(content, "__getitem__")
            ):
                content = eval(
                    "content.__getitem__(%s)" % match.strip("[]"), {}, locals()
                )
            else:
                content = eval(comment.sub("", str(key)), {}, frame_locals)

        # requirements for content to be valid
        if content is not None and kwargs["class"] in cls.DUMP_CLASS:
            dump = pickle.dumps(content)
            if not overwrite:
                # rename file if necessary
                while True:
                    if (
                        not target.exists()
                        or hashlib.md5(target.read_bytes()).digest()
                        == hashlib.md5(dump).digest()
                    ):
                        break
                    kwargs["cnt"] += 1
                    target = cls.MOCK_DIR / tmpl.format(**kwargs)
            # save content
            target.write_bytes(dump)

        else:
            # class is not supported or content has not been identified correctly
            return

        # return path to the dumped file
        return target

    @classmethod
    def __read__(cls, fname: Union[str, Path]):
        """
        Reads dump a file from local drive.

        Positional arguments:
            fname, Union[str, Path],
                file name.
        """

        if isinstance(fname, Path):
            target = fname
        else:
            target = cls.MOCK_DIR / (
                str(fname).endswith(".dump") and fname or f"{fname}.dump"
            )
        if target.exists():
            return pickle.loads(target.read_bytes())
        raise KeyError(dump4mock.MOCK_DIR, fname)

    @classmethod
    def __clear__(cls, dump_class: tuple[str] = None):
        """
        Removes dumped files.

        Positional arguments:
            dump_class: tuple[str],
                list of classes for which the dump files should be removed.
        """

        for name in dump_class and dump_class or cls.DUMP_CLASS:
            for file in cls.MOCK_DIR.glob(f"{name}.*.dump"):
                file.unlink()


if __name__ == "__main__":
    help(dump4mock)
