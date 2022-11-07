# -*- coding: utf-8 -*-

import hashlib
from inspect import stack
from pathlib import Path
from typing import Union

import dill as pickle


class MockDumper:
    """
    Internal tool to dump any PYthon object to local drive.
    """

    # enable/disable globally for selected class instances
    DUMP_CLASS = ["Authenticator"]
    # location for dumped files
    MOCK_DIR = Path(__file__).parent / "mock"

    @staticmethod
    def dump(key: str, overwrite: bool = False) -> Path:
        """
        Dumps Python object into local drive.
        Object is identified by the key within the local namespace of given frame.

        Positional arguments:
            key: str.

            overwrite: bool,
                if True, the dump file will be overwritten.
        """

        frames = stack()
        frame_locals = frames[1][0].f_locals
        tmpl, kwargs = "{class}.{method}.{key}#{cnt}.dump", {
            "class": frame_locals.get("self")
            and frame_locals["self"].__class__.__name__
            or "root",
            "method": frames[1].function,
            "cnt": 1,
            "key": key,
        }
        target = MockDumper.MOCK_DIR / tmpl.format(**kwargs)
        content = frame_locals.get(key.split(".")[0])
        if len(key.split(".")) > 1:
            for attr in key.split(".")[1:]:
                content = getattr(content, attr, content)
        if content is not None and kwargs["class"] in MockDumper.DUMP_CLASS:
            dump = pickle.dumps(content)
            while True:
                if (
                    not target.exists()
                    or hashlib.md5(target.read_bytes()).digest()
                    == hashlib.md5(dump).digest()
                ):
                    break
                kwargs["cnt"] += 1
                target = MockDumper.MOCK_DIR / tmpl.format(**kwargs)
            target.write_bytes(dump)
        elif overwrite:
            target.write_bytes(dump)
        return target

    @staticmethod
    def read(fname: Union[str, Path]):
        """
        Reads dump a file from local drive.

        Positional arguments:
            fname, str,
                file name.
        """
        if isinstance(fname, Path):
            target = fname
        else:
            target = MockDumper.MOCK_DIR / fname
        if target.exists:
            return pickle.loads(target.read_bytes())
        raise KeyError(fname)

    @staticmethod
    def clear():
        """
        Removes dumped files.
        """
        for name in MockDumper.DUMP_CLASS:
            for file in MockDumper.MOCK_DIR.glob(f"{name}*.dump"):
                file.unlink()


if __name__ == "__main__":
    MockDumper.clear()
