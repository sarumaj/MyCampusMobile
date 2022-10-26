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

from .logger import Logger

class CacheTestCase(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.gettempdir()
        self.logger_name = Path(temp_dir).name
        self.logger = Logger(
            filepath=temp_dir, 
            verbose=True
        )

    def test_logging(self):
        with self.assertLogs(self.logger_name, level='DEBUG') as cm:
            self.logger.info("hello")
            self.logger.debug("world")
            self.assertEqual(
                cm.output, 
                [f'INFO:{self.logger_name}:hello', f'DEBUG:{self.logger_name}:world'],
                "failed to log"
            )

if __name__ == "__main__":
    unittest.main()