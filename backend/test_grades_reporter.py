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

from .dumper import dump4mock
from .grades_reporter import GradesReporter


class GradesReporterTestCase(unittest.TestCase):
    client = GradesReporter(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=True,
    )

    @patch.object(client, "_session")
    def test_get_grades(self, session_mock):
        session_mock.get.side_effect = (
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "GradesReporter.get_grades.response.text"
                    "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Flocal%2Fiubh_ac5sso%2Fac5notenuebersicht.php)#1"
                ],
            ),
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "GradesReporter.get_grades.response.text@session.get(utl)#1"
                ],
            ),
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "GradesReporter.get_grades.response.text"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fen%2Fexaminations%2Fexamination-results.php)#1"
                ],
            ),
        )

        self.assertEqual(
            self.client.get_grades(),
            dump4mock["GradesReporter.get_grades.result#1"],
        )


if __name__ == "__main__":
    unittest.main()
