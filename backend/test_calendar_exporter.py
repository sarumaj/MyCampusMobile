# -*- coding: utf-8 -*-

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################


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
from .dumper import dump4mock


class CalendarExporterTestCase(unittest.TestCase):
    client = CalendarExporter(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=True,
    )

    @patch.object(client, "_session")
    def test_calendar_export(self, session_mock):
        session_mock.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "CalendarExporter.export_calendar.response.text"
                "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fcalendar%2Fexport.php)#1"
            ],
        )
        session_mock.post.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "CalendarExporter.export_calendar.response.text"
                "@session.post(https%3A%2F%2Fmycampus.iubh.de%2Fcalendar%2Fexport.php,"
                "data=form)#1"
            ],
        )
        self.assertEqual(
            self.client.export_calendar(),
            (
                dump4mock["CalendarExporter.export_calendar.fname#1"],
                dump4mock["CalendarExporter.export_calendar.result#1"],
            ),
        )


if __name__ == "__main__":
    unittest.main()
