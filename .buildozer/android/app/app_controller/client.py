# -*- coding: utf-8 -*-

from .calendar_exporter import CalendarExporter
from .course_browser import CourseBrowser
from .downloader import Downloader
from .grades_reporter import GradesReporter

###############
#             #
# definitions #
#             #
###############


class Client(CalendarExporter, CourseBrowser, Downloader, GradesReporter):
    """
    Controller accessing the model (MyCampus).
    Inherits from:
        CalendarExporter,
        CourseBrowser,
        Downloader,
        GradesReporter.
    """
