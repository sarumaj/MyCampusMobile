# -*- coding: utf-8 -*-

import unittest

import backend.tests

if __name__ == "__main__":
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromModule(backend.tests))
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
