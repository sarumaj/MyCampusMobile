# -*- coding: utf-8 -*-

import tempfile
import unittest
from unittest.mock import MagicMock, patch

from backend.course_browser import CourseBrowser
from backend.dumper import dump4mock


class CourseBrowserTestCase(unittest.TestCase):
    client = CourseBrowser(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=False,
        emit=False,
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
    def test_get_booking_id(self, session_mock):
        get_side_effects = [
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "CourseBrowser.get_booking_id.response.text"
                    "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Flocal%2Fiubh_ac5sso%2Fac5kursbuchung.php)#1"
                ],
            ),
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "CourseBrowser.get_booking_id.response.text"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fen%2Fstudy%2Fcurricular-course-registration.php)#1"
                ],
            ),
        ]
        if dump4mock[
            "CourseBrowser.get_booking_id.is_get"
            "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Flocal%2Fiubh_ac5sso%2Fac5kursbuchung.php)#1"
        ]:
            get_side_effects.insert(1, MagicMock())
        else:
            session_mock.post.return_value = MagicMock()
        session_mock.get.side_effect = get_side_effects
        self.assertEqual(
            self.client.get_booking_id(),
            dump4mock["CourseBrowser.get_booking_id.booking_id#1"],
        )

    @patch.object(client, "_session")
    def test_get_graded_records(self, session_mock):
        self.client[f"{self.client.username}.booking_id"] = dump4mock[
            "CourseBrowser.get_booking_id.booking_id#1"
        ]
        session_mock.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_graded_records.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2FCourseInscriptionCurricular"
                    "%2FDefaultController%2FfetchCurriculumGrades)#1"
                ]
            ),
        )
        passed_modules, passed_subjects = self.client.get_graded_records()
        self.assertSetEqual(
            passed_modules,
            dump4mock["CourseBrowser.get_graded_records.passed_modules#1"],
        )
        self.assertSetEqual(
            passed_subjects,
            dump4mock["CourseBrowser.get_graded_records.passed_subjects#1"],
        )

    @patch.object(client, "_session")
    def test_get_curricullum_entries(self, session_mock):
        self.client[f"{self.client.username}.booking_id"] = dump4mock[
            "CourseBrowser.get_booking_id.booking_id#1"
        ]
        session_mock.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_curricullum_entries.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCurriculumEntry)#1"
                ]
            ),
        )
        self.assertEqual(
            self.client.get_curricullum_entries(set(), set()),
            dump4mock[
                "CourseBrowser.get_curricullum_entries.curriculum_entries"
                "@passed_modules=d751713988987e9331980363e24189ce"
                "@passed_subjects=d751713988987e9331980363e24189ce#1"
            ],
        )
        self.assertEqual(
            self.client.get_curricullum_entries(
                {"1906", "1361", "1362", "1919", "1908", "1865"},
                {
                    "10002127",
                    "10001700",
                    "10001894",
                    "10001634",
                    "10001633",
                    "10002126",
                },
            ),
            dump4mock[
                "CourseBrowser.get_curricullum_entries.curriculum_entries"
                "@passed_modules=acd77056f794b8bfd5d81ecab5cae563"
                "@passed_subjects=22db950f69dd55205c41b36b463d72d5#1"
            ],
        )

    @patch.object(client, "_session")
    def test_get_dependency_graph(self, session_mock):
        self.client[f"{self.client.username}.booking_id"] = dump4mock[
            "CourseBrowser.get_booking_id.booking_id#1"
        ]
        session_mock.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_dependency_graph.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCurriculumEntry)#1"
                ]
            ),
        )
        self.client.get_dependency_graph()

    @patch.object(client, "_session")
    def test_create_booking_context(self, session_mock):
        self.client[f"{self.client.username}.booking_id"] = dump4mock[
            "CourseBrowser.get_booking_id.booking_id#1"
        ]
        session_mock.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.create_booking_context.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCourses)#1"
                ]
            ),
        )
        self.maxDiff = None
        self.assertDictEqual(
            self.client.create_booking_context(
                dump4mock[
                    "CourseBrowser.get_curricullum_entries.curriculum_entries"
                    "@passed_modules=d751713988987e9331980363e24189ce"
                    "@passed_subjects=d751713988987e9331980363e24189ce#1"
                ]
            ),
            dump4mock[
                "CourseBrowser.create_booking_context.curriculum_entries"
                "@c962c8ef98d663d10669cd42d274bdd4#1"
            ],
        )
        self.assertDictEqual(
            self.client.create_booking_context(
                dump4mock[
                    "CourseBrowser.get_curricullum_entries.curriculum_entries"
                    "@passed_modules=acd77056f794b8bfd5d81ecab5cae563"
                    "@passed_subjects=22db950f69dd55205c41b36b463d72d5#1"
                ]
            ),
            dump4mock[
                "CourseBrowser.create_booking_context.curriculum_entries"
                "@c6dead190aac86d2a7ca1dc00ca424a9#1"
            ],
        )

    @patch.object(client, "_session")
    def test_update_enrolled_course_modules(self, session_mock):
        self.client[f"{self.client.username}.booking_id"] = dump4mock[
            "CourseBrowser.get_booking_id.booking_id#1"
        ]
        session_mock.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.update_enrolled_course_modules.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCourseTickets)#1"
                ]
            ),
        )
        self.maxDiff = None
        self.assertDictEqual(
            self.client.update_enrolled_course_modules(
                dump4mock[
                    "CourseBrowser.create_booking_context.curriculum_entries"
                    "@c962c8ef98d663d10669cd42d274bdd4#1"
                ]
            ),
            dump4mock[
                "CourseBrowser.update_enrolled_course_modules.curriculum_entries"
                "@1cac2404164632ca5604c20ae17fdc20#1"
            ],
        )
        self.assertDictEqual(
            self.client.update_enrolled_course_modules(
                dump4mock[
                    "CourseBrowser.create_booking_context.curriculum_entries"
                    "@c6dead190aac86d2a7ca1dc00ca424a9#1"
                ]
            ),
            dump4mock[
                "CourseBrowser.update_enrolled_course_modules.curriculum_entries"
                "@f7802cbe1255f74ca6aa4a751a07d2b1#1"
            ],
        )

    @patch.object(client, "_session")
    def test_available_credits(self, session_mock):
        self.client[f"{self.client.username}.booking_id"] = dump4mock[
            "CourseBrowser.get_booking_id.booking_id#1"
        ]
        session_mock.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_available_credits.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCreditCounts)#1"
                ]
            ),
        )
        self.maxDiff = None
        self.assertDictEqual(
            self.client.get_available_credits(),
            dump4mock[
                "CourseBrowser.get_available_credits.response.json"
                "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                "CourseInscriptionCurricular%2FDefaultController%2FfetchCreditCounts)#1"
            ],
        )

    @patch.object(client, "_session")
    def test_get_courses_to_register(self, session_mock):
        self.client[f"{self.client.username}.booking_id"] = dump4mock[
            "CourseBrowser.get_booking_id.booking_id#1"
        ]
        session_mock.get.side_effect = (
            MagicMock(
                status_code=200,
                json=MagicMock(
                    return_value=dump4mock[
                        "CourseBrowser.get_graded_records.response.json"
                        "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2FCourseInscriptionCurricular"
                        "%2FDefaultController%2FfetchCurriculumGrades)#1"
                    ]
                ),
            ),
            MagicMock(
                status_code=200,
                json=MagicMock(
                    return_value=dump4mock[
                        "CourseBrowser.get_curricullum_entries.response.json"
                        "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                        "CourseInscriptionCurricular%2FDefaultController%2FfetchCurriculumEntry)#1"
                    ]
                ),
            ),
            MagicMock(
                status_code=200,
                json=MagicMock(
                    return_value=dump4mock[
                        "CourseBrowser.create_booking_context.response.json"
                        "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                        "CourseInscriptionCurricular%2FDefaultController%2FfetchCourses)#1"
                    ]
                ),
            ),
            MagicMock(
                status_code=200,
                json=MagicMock(
                    return_value=dump4mock[
                        "CourseBrowser.update_enrolled_course_modules.response.json"
                        "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                        "CourseInscriptionCurricular%2FDefaultController%2FfetchCourseTickets)#1"
                    ]
                ),
            ),
            MagicMock(
                status_code=200,
                json=MagicMock(
                    return_value=dump4mock[
                        "CourseBrowser.get_available_credits.response.json"
                        "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                        "CourseInscriptionCurricular%2FDefaultController%2FfetchCreditCounts)#1"
                    ]
                ),
            ),
        )
        self.maxDiff = None
        self.assertDictEqual(
            self.client.get_courses_to_register(),
            dump4mock["CourseBrowser.get_courses_to_register.result#1"],
        )
