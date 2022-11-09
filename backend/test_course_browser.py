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

from .course_browser import CourseBrowser
from .dumper import dump4mock


class GradesReporterTestCase(unittest.TestCase):
    client = CourseBrowser(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=True,
    )

    @patch.object(client, "_session")
    def test_list_courses_and_list_course_resources(self, session_mock):
        session_mock.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "CourseBrowser.list_courses.response.text"
                "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fmy%2F)#1"
            ],
        )
        courses = self.client.list_courses()
        self.assertEqual(
            courses,
            dump4mock["CourseBrowser.list_courses.result#1"],
        )
        for course in courses:
            session_mock.get.return_value = MagicMock(
                status_code=200,
                text=dump4mock[
                    "CourseBrowser.list_course_resources.response.text"
                    "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fcourse%2Fview.php,"
                    f"params={{course_id={course['id']}}})#1"
                ],
            )
            self.assertEqual(
                self.client.list_course_resources(course["id"]),
                dump4mock[
                    f"CourseBrowser.list_course_resources.result@course_id={course['id']}#1"
                ],
            )

    @patch.object(client, "_session")
    def _test_get_booking_id(self, session_mock):
        session_mock.get.side_effect = (
            MagicMock(
                status_code=200,
                return_value=dump4mock[""]
            )
        )


if __name__ == "__main__":
    unittest.main()
