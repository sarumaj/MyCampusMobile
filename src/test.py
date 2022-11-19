# -*- coding: utf-8 -*-

import unittest

from backend import tests

if __name__ == "__main__":
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromModule(tests))
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
