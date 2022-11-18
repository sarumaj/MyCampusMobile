# -*- coding: utf-8 -*-

import tempfile
import unittest
from unittest.mock import MagicMock, patch

from backend.dumper import dump4mock
from backend.grades_reporter import GradesReporter


class GradesReporterTestCase(unittest.TestCase):
    client = GradesReporter(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=False,
        emit=False,
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
                    "GradesReporter.get_grades.response.text@session.get(url)#1"
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

        self.assertDictEqual(
            self.client.get_grades(),
            dump4mock["GradesReporter.get_grades.result#1"],
        )
