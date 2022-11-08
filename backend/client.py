# -*- coding: utf-8 -*-

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = ".".join(parent.parts[len(top.parts) :])

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
