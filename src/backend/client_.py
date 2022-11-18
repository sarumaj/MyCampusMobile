# -*- coding: utf-8 -*-

from collections import OrderedDict
from typing import Any, Generator, Optional, Union
from unittest.mock import MagicMock

import networkx as nx

from .calendar_exporter import ExportEvents, TimePeriod
from .client import Client
from .dumper import dump4mock

###############
#             #
# definitions #
#             #
###############


class Client_(Client):
    """
    Mock instance for the client.Client
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = MagicMock()

    def get_saml_request(self) -> str:
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "Authenticator.get_saml_request.response.text"
                "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fmy)#1"
            ],
        )
        return super().get_saml_request()

    def get_saml_response(self, SAMLrequest: str) -> str:
        self._session.post.side_effect = (
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "Authenticator.get_saml_response.response.text"
                    "@session.post(https%3A%2F%2Flogin.iubh.de%2Fidp%2Fprofile%2FSAML2%2FPOST%2FSSO,"
                    "data=SAMLrequest)#1"
                ],
            ),
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "Authenticator.get_saml_response.response.text"
                    "@session.post(https%3A%2F%2Flogin.iubh.de%2Fidp%2Fprofile%2FSAML2%2FPOST%2FSSO,"
                    "data=form)#1"
                ],
            ),
        )
        return super().get_saml_response(SAMLrequest)

    def submit_saml_response(self, SAMLresponse: str):
        self._session.post.side_effect = None
        self._session.post.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "Authenticator.submit_saml_response.response.text"
                "@session.post(https%3A%2F%2Fmycampus.iubh.de%2Fauth%2Fsaml2%2Fsp%2Fsaml2-acs.php%2Fmycampus.iubh.de,"
                "data=SAMLresponse)#1"
            ],
        )
        return super().submit_saml_response(SAMLresponse)

    def close(self):
        self._session.get.side_effect = (
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "Authenticator.close.response.text"
                    "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fmy%2F)#1"
                ],
            ),
            MagicMock(
                status_code=200,
                text=dump4mock[
                    "Authenticator.close.response.text@session.get(logout)#1"
                ],
            ),
        )
        return super().close()

    def export_calendar(
        self,
        *,
        exportevents: ExportEvents = ExportEvents["all"],
        timeperiod: TimePeriod = TimePeriod["recentupcoming"],
        cached: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "CalendarExporter.export_calendar.response.text"
                "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fcalendar%2Fexport.php)#1"
            ],
        )
        self._session.post.side_effect = None
        self._session.post.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "CalendarExporter.export_calendar.response.text"
                "@session.post(https%3A%2F%2Fmycampus.iubh.de%2Fcalendar%2Fexport.php,"
                "data=form)#1"
            ],
        )
        return super().export_calendar(
            exportevents=exportevents, timeperiod=timeperiod, cached=cached
        )

    def list_courses(self, *, cached: bool = False) -> list[dict]:
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "CourseBrowser.list_courses.response.text"
                "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fmy%2F)#1"
            ],
        )
        return super().list_courses(cached=cached)

    def list_course_resources(
        self, course_id: int, *, cached: bool = False
    ) -> list[dict]:
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "CourseBrowser.list_course_resources.response.text"
                "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fcourse%2Fview.php,"
                f"params={{course_id={course_id}}})#1"
            ],
        )
        return super().list_course_resources(course_id, cached=cached)

    def enroll(
        self,
        *,
        enrolmentPeriodId: str,
        lectureSeriesId: str,
        assignedSubjectIds: str,
        curriculumEntryId: str,
        bookingId: str,
    ):
        self._session.post.status_code = 200
        return super().enroll(
            enrolmentPeriodId=enrolmentPeriodId,
            lectureSeriesId=lectureSeriesId,
            assignedSubjectIds=assignedSubjectIds,
            curriculumEntryId=curriculumEntryId,
            bookingId=bookingId,
        )

    def cancel(
        self,
        *,
        enrolmentPeriodId: str,
        lectureSeriesId: str,
        curriculumEntryId: str,
        bookingId: str,
        **kwargs,
    ):
        self._session.post.status_code = 200
        return super().cancel(
            enrolmentPeriodId=enrolmentPeriodId,
            lectureSeriesId=lectureSeriesId,
            curriculumEntryId=curriculumEntryId,
            bookingId=bookingId,
            **kwargs,
        )

    def dispatch(
        self,
        *,
        enrolmentPeriodId: str,
        lectureSeriesId: str,
        curriculumEntryId: str,
        bookingId: str,
        **kwargs,
    ):
        self._session.get.status_code = 200
        return super().dispatch(
            enrolmentPeriodId=enrolmentPeriodId,
            lectureSeriesId=lectureSeriesId,
            curriculumEntryId=curriculumEntryId,
            bookingId=bookingId,
            **kwargs,
        )

    def get_booking_id(self) -> str:
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
            self._session.post.return_value = MagicMock()
        self._session.get.side_effect = get_side_effects
        return super().get_booking_id()

    def get_graded_records(self) -> tuple[set[str]]:
        self.get_booking_id()
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_graded_records.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2FCourseInscriptionCurricular"
                    "%2FDefaultController%2FfetchCurriculumGrades)#1"
                ]
            ),
        )
        return super().get_graded_records()

    def get_curricullum_entries(
        self, passed_modules: set[str], passed_subjects: set[str]
    ) -> OrderedDict:
        self.get_booking_id()
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_curricullum_entries.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCurriculumEntry)#1"
                ]
            ),
        )
        return super().get_curricullum_entries(passed_modules, passed_subjects)

    def get_dependency_graph(
        self, *, cached: bool = False, include_root: bool = False
    ) -> nx.Graph:
        self.get_booking_id()
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_dependency_graph.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCurriculumEntry)#1"
                ]
            ),
        )
        return super().get_dependency_graph(cached=cached, include_root=include_root)

    def create_booking_context(self, curriculum_entries: OrderedDict) -> OrderedDict:
        self.get_booking_id()
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.create_booking_context.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCourses)#1"
                ]
            ),
        )
        return super().create_booking_context(curriculum_entries)

    def update_enrolled_course_modules(
        self, curriculum_entries: OrderedDict
    ) -> OrderedDict:
        self.get_booking_id()
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.update_enrolled_course_modules.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCourseTickets)#1"
                ]
            ),
        )
        return super().update_enrolled_course_modules(curriculum_entries)

    def get_available_credits(self) -> dict[str, int]:
        self.get_booking_id()
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=dump4mock[
                    "CourseBrowser.get_available_credits.response.json"
                    "@session.get(https%3A%2F%2Fcare-fs.iubh.de%2Fajax%2F4713%2F"
                    "CourseInscriptionCurricular%2FDefaultController%2FfetchCreditCounts)#1"
                ]
            ),
        )
        return super().get_available_credits()

    def get_courses_to_register(self, cached: bool = False) -> dict:
        self.get_booking_id()
        self._session.get.side_effect = (
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
        return super().get_courses_to_register(cached=cached)

    def download(
        self, link: str, cached: Optional[bool] = False, chunk: Optional[int] = None
    ) -> tuple[str, Union[bytes, Generator[bytes, None, None]], int]:
        self._session.get.side_effect = None
        self._session.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock["Downloader.download.response.text@session.get(link)#1"],
            headers=dump4mock[
                "Downloader.download.response.headers@session.get(link)#1"
            ],
            content=dump4mock[
                "Downloader.download.response.content@session.get(link)#1"
            ],
        )
        return super().download(link, cached, chunk)

    def get_grades(self, cached: bool = False) -> OrderedDict:
        self._session.get.side_effect = (
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
        return super().get_grades(cached)
