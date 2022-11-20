# -*- coding: utf-8 -*-

import tempfile
import unittest
from pathlib import Path

from ..logger import Logger


class LoggerTestCase(unittest.TestCase):
    def setUp(self):
        temp_dir = tempfile.mkdtemp()
        self.logger_name = Path(temp_dir).name
        self.logger = Logger(filepath=temp_dir, verbose=True)

    def test_logging(self):
        with self.assertLogs(self.logger_name, level="DEBUG") as cm:
            self.logger.info("hello")
            self.logger.debug("world")
            self.assertEqual(
                cm.output,
                [f"INFO:{self.logger_name}:hello", f"DEBUG:{self.logger_name}:world"],
                "failed to log",
            )
