# -*- coding: utf-8 -*-

import hashlib
import re
from inspect import getmembers, getmro, isfunction, stack, ismethod
from pathlib import Path
from typing import Any, Union

import dill as pickle


class __dump4mockMeta__(type):
    """
    Meta class making the implementing class subscriptable.
    """

    def __getitem__(cls, x: Union[str, Path]):
        if hasattr(cls, "__read__") and isinstance(x, (str, Path)):
            return cls.__read__(x)
        raise KeyError(x)


class dump4mock(metaclass=__dump4mockMeta__):
    """
    Internal tool to dump any PYthon object to local drive.
    It can be used as function or subscriptable object.
    """

    # enable/disable globally for selected class instances
    DUMP_CLASS = [
        "Authenticator",
        "CalendarExporter",
        "CourseBrowser",
        "Downloader",
        "GradesReporter",
    ]
    # location for dumped files
    MOCK_DIR = Path(__file__).parents[1] / "data" / "mock"

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
            or (
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

        # simplify key in order to prevent violation of allowed filename charset
        subscription = re.compile(r"(\(.*\)|\[.+\])(?=@)")
        base = subscription.sub("", str(key), 1)

        # template for the file name and keyword mapping for formatting
        tmpl, kwargs = "{class}.{method}.{key}#{cnt}.dump", {
            "class": frame_locals.get("self")
            and frame_locals["self"].__class__.__name__
            or frame_locals.get("cls")
            and frame_locals["cls"].__name__
            or "root",
            "method": frames[context].function,
            "cnt": 1,
            "key": base,
        }

        # apply method resolution order
        def apply_mro(cls):
            # apply MRO on class level and not instance level
            for cls_object in getmro(cls):
                # retrieve methods (for class level identified as function objects)
                for name, _ in getmembers(cls_object, predicate=lambda o: isfunction(o) or ismethod(o)):
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
        base = re.sub("@(.*)$", "", base)
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
            content = eval("content%s" % subscription.search(str(key)).group(1))

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
            raise KeyError(key)

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
        raise KeyError(fname)

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

class Test:
    @classmethod
    def test(cls2, idx):
        val = list(range(10))
        dump4mock("val[%(c)d]@test(idx=%(c)d),test(idx=%(c)d)@test(idx=%(c)d)" % {'c':idx})
        return val[idx]

class Child(Test):
    pass

if __name__ == "__main__":
    #help(dump4mock)
    dump4mock.DUMP_CLASS.extend(['Child', 'Test'])
    Child().test(1)
    print(dump4mock["Child.test.val@test(idx=%(c)d),test(idx=%(c)d)@test(idx=%(c)d)#1" % {'c':1}])
