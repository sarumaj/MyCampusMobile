# -*- coding: utf-8 -*-

import unittest

from app_controller.tests.test_auth import AuthenticatorTestCase
from app_controller.tests.test_cache import CacheTestCase
from app_controller.tests.test_calendar_exporter import CalendarExporterTestCase
from app_controller.tests.test_course_browser import CourseBrowserTestCase
from app_controller.tests.test_downloader import DownloaderTestCase
from app_controller.tests.test_dumper import DumperTestCase
from app_controller.tests.test_exceptions import ExceptionsTestCase
from app_controller.tests.test_grades_reporter import GradesReporterTestCase
from app_controller.tests.test_logger import LoggerTestCase


def mock_app():
    import os
    from pathlib import Path

    import certifi

    os.environ["KIVY_IMAGE"] = "pil,sdl2"
    os.environ["SSL_CERT_FILE"] = certifi.where()

    from kivy.core.window import Window

    Window.size = (720, 1440)
    Window.minimum_height = 1000
    Window.minimum_width = 600

    from app_controller.client_ import Client_ as Client
    from app_view.app import MobileApp
    from app_view.platform_specs import app_dir_path

    app = MobileApp(
        Client(
            "",
            "",
            max_len=100,
            max_age=60**2,
            filepath=__file__,
            verbose=True,
            destination=str(Path(app_dir_path) / ".cache.dat"),
        )
    )
    app.run()


if __name__ == "__main__":
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(AuthenticatorTestCase))
    suite.addTests(loader.loadTestsFromTestCase(CacheTestCase))
    suite.addTests(loader.loadTestsFromTestCase(CalendarExporterTestCase))
    suite.addTests(loader.loadTestsFromTestCase(CourseBrowserTestCase))
    suite.addTests(loader.loadTestsFromTestCase(DownloaderTestCase))
    suite.addTests(loader.loadTestsFromTestCase(DumperTestCase))
    suite.addTests(loader.loadTestsFromTestCase(ExceptionsTestCase))
    suite.addTests(loader.loadTestsFromTestCase(GradesReporterTestCase))
    suite.addTests(loader.loadTestsFromTestCase(LoggerTestCase))
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
    if len(result.errors) + len(result.unexpectedSuccesses) == 0:
        mock_app()
