# -*- coding: utf-8 -*-

import re
import sys
from functools import partial
from pathlib import Path

import networkx as nx
from bs4 import BeautifulSoup

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

from .auth import Authenticator
from .exceptions import ExceptionHandler, RequestFailed

###############
#             #
# definitions #
#             #
###############


class CourseBrowser(Authenticator):
    """
    Implements methods to browse student's enrolled courses and course resources.
    """

    @ExceptionHandler("failed to obtain course list", RequestFailed)
    def list_courses(self, *, cached: bool = False) -> list[dict]:
        """
        Lists active and inactive courses.

        Keyword arguments:
            cached: bool, default is False,
                if True, response will be retrieved from cache.

        Returns:
            list[dict]:
            [
                {
                    "fullname": str,
                    "shortname": str,
                    "id": int,
                    "state": str,
                    "img": str
                }, ...
            ]
        """

        if cached and self.get(f"{self.username}.courses") is not None:
            return self[f"{self.username}.courses"]

        self.debug("Requesting course list")
        response = partial(self._session.get, "https://mycampus.iubh.de/my/")()
        soup = BeautifulSoup(response.text, "html.parser")
        result = [
            {
                "fullname": el.find("div", class_="fullname").text,
                "shortname": el.find("div", class_="shortname").text,
                "id": int(re.sub(r"(?:.*?\?id=)([^&]*).*", "\\1", el.get("href"))),
                "state": re.sub("courses-", "", el.parent.get("id")),
                "img": el.find("img", class_="courseimage").get("src"),
            }
            for el in [
                *soup.find("div", id="courses-active").find_all(
                    "a", class_="courseitem"
                ),
                *soup.find("div", id="courses-inactive").find_all(
                    "a", class_="courseitem"
                ),
            ]
        ]
        self[f"{self.username}.courses"] = result
        self.debug("Successfully retrieved course list")
        return result

    @ExceptionHandler("failed to obtain course resources", RequestFailed)
    def list_course_resources(
        self, course_id: int, *, cached: bool = False
    ) -> list[dict]:
        """
        Lists course resources.

        Positional arguments:
            course_id: int,
                id of given course module corresponding with list item
                from the result set of the method list_courses.

        Keyword arguments:
            cached: bool, default is False,
                if True, response will be retrieved from cache.

        Returns:
            list[dict]:
            [
                {
                    "link": str,
                    "title": str
                }
            ]

        """

        if cached and self.get(f"{self.username}.resources", {}).get(course_id):
            return self[f"{self.username}.resources"][course_id]

        self.debug(f"Requesting course view for {course_id}")

        response = partial(
            self._session.get,
            "https://mycampus.iubh.de/course/view.php",
            params={"id": course_id},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )

        soup = BeautifulSoup(response.text, "html.parser")
        result = {
            **self.get(f"{self.username}.resources", dict()),
            **{
                course_id: [
                    {"link": el.get("href"), "title": el.text}
                    for el in (
                        *soup.select(
                            'a[href^="https://mycampus.iubh.de/mod/resource/view.php"]'
                        ),
                        *soup.select(
                            'a[href^="https://mycampus.iubh.de/local/downloadprettyfier/view.php"]'
                        ),
                    )
                ]
            },
        }
        self[f"{self.username}.resources"] = result
        self.debug("Successfully retrieved course view")
        return result[course_id]

    @ExceptionHandler("failed to enroll", RequestFailed)
    def enroll(
        self,
        *,
        enrolmentPeriodId: str,
        lectureSeriesId: str,
        assignedSubjectIds: str,
        curriculumEntryId: str,
        bookingId: str,
    ):
        """
        Sends HTTP request to corresponding endpoint to enroll in a given course module.

        Keyword arguments:
            arguments provided by the method "create_booking_context".
        """

        self.debug(f"Sending enroll request for curriculum entry: {curriculumEntryId}")
        response = partial(
            self._session.post,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/BookCourse",
            params={
                "enrolmentPeriodId": enrolmentPeriodId,
                "lectureSeriesId": lectureSeriesId,
                "assignedSubjectIds": assignedSubjectIds,
                "curriculumEntryId": curriculumEntryId,
                "bookingId": bookingId,
            },
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        self.debug("Successfully enrolled")

    @ExceptionHandler("failed to cancel", RequestFailed)
    def cancel(
        self,
        *,
        enrolmentPeriodId: str,
        lectureSeriesId: str,
        curriculumEntryId: str,
        bookingId: str,
        **kwargs,
    ):
        """
        Sends HTTP request to corresponding endpoint to cancel enrollment in a given course module.

        Keyword arguments:
            arguments provided by the method "create_booking_context".
        """

        self.debug(f"Canceling enrollment for curriculum entry: {curriculumEntryId}")
        response = partial(
            self._session.post,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/CancelBooking",
            params={
                "enrolmentPeriodId": enrolmentPeriodId,
                "lectureSeriesId": lectureSeriesId,
                "assignedSubjectIds": "",
                "curriculumEntryId": curriculumEntryId,
                "bookingId": bookingId,
            },
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )()
        assert response.status_code == 200, (
            "server responded with %d" % response.status_code
        )
        self.debug("Successfully cancelled enrollment")

    @ExceptionHandler("failed to start", RequestFailed)
    def dispatch(
        self,
        *,
        enrolmentPeriodId: str,
        lectureSeriesId: str,
        curriculumEntryId: str,
        bookingId: str,
        **kwargs,
    ):
        """
        Sends HTTP request to corresponding endpoint to start a given course module.

        Keyword arguments:
            arguments provided by the method "create_booking_context".
        """

        self.debug(f"Sending request to begin curriculum entry: {curriculumEntryId}")
        response = partial(
            self._session.post,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/BookCourse",
            params={
                "enrolmentPeriodId": enrolmentPeriodId,
                "lectureSeriesId": lectureSeriesId,
                "assignedSubjectIds": "",
                "curriculumEntryId": curriculumEntryId,
                "bookingId": bookingId,
            },
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        self.debug("Successfully started course module")

    @ExceptionHandler("failed to get booking id", RequestFailed)
    def get_booking_id(self) -> str:
        """
        Retrieves booking id needed for various operation related to course management.

        Returns:
            str:
                Booking id.
        """

        self.debug("Retrieving booking id")
        # get course registration context
        response = partial(
            self._session.get,
            "https://mycampus.iubh.de/local/iubh_ac5sso/ac5kursbuchung.php",
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        try:
            # set course registration context
            regex = re.compile(
                "("
                + re.escape("https://care-fs.iubh.de/img/mycsso/set.php")
                + '.*?)(?=")'
            )
            response = partial(
                self._session.get, re.search(regex, response.text).group(1)
            )()
        except BaseException:
            self.warning("failed to set context for booking id")
        finally:
            # retrieve booking id
            response = partial(
                self._session.get,
                "https://care-fs.iubh.de/en/study/curricular-course-registration.php",
            )()
            regex = re.compile(
                r'\{"id":"(\d+)","classId":"\d+",'
                r'"studyProgramId":"\d+","focusIds":\[.*\]\}'
            )
            booking_id = regex.search(response.text).group(1)
            self[f"{self.username}.booking_id"] = booking_id
            self.debug(f"Retrieved booking id: {booking_id}")
            return booking_id

    @ExceptionHandler("failed to request graded curriculum entries", RequestFailed)
    def get_graded_records(self) -> tuple[set[str]]:
        """
        Retrieves graded curriculum entries:

        Returns:
            tuple[set[str]]:
            (
                {module_id, ...},
                {subject_id, ...}
            )
        """

        # make sure to have valid booking id
        if not self.get(f"{self.username}.booking_id"):
            self.get_booking_id()

        self.debug("Requesting graded curriculum entries")
        response = partial(
            self._session.get,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/fetchCurriculumGrades",
            params={"bookindId": self.get(f"{self.username}.booking_id")},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        passed_modules, passed_subjects = set(), set()
        for grade in response.json():
            if grade.get("moduleId"):
                passed_modules.add(str(grade["moduleId"]))
            if grade.get("subjectId"):
                passed_subjects.add(str(grade["subjectId"]))
        self.debug("Successfully retrieved graded records")
        return passed_modules, passed_subjects

    @ExceptionHandler("failed to request curriculum entries", RequestFailed)
    def get_curricullum_entries(
        self, passed_modules: set[str], passed_subjects: set[str]
    ) -> dict:
        """
        Retrieves curriculum entries.

        Positional arguments:
            originate with the result set of the method "get_graded_records".

        Returns:
            dict
            {
                semester: {
                    curriculum entry id: {
                        "label": str
                        "credits": int
                        "children": {
                            id: {
                                "credits": int,
                                "label": str,
                                "subjectId": str,
                                "isStarted": bool
                            }
                        },
                        "presupposedModuleIds": [moduleId, ...],
                        "moduleId": str,
                        "isEnrolled": bool
                    }
                }, ...
            }
        """

        # make sure to have valid booking id
        if not self.get(f"{self.username}.booking_id"):
            self.get_booking_id()

        self.debug("Requesting curriculum entries")
        response = partial(
            self._session.get,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/fetchCurriculumEntry",
            params={"bookindId": self.get(f"{self.username}.booking_id")},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        curriculum_entries = {
            semester["label"]: {
                "subjects": {
                    entry["id"]: {
                        **{
                            ekey: (
                                entry[ekey]
                                if ekey != "children"
                                else {
                                    child["id"]: {
                                        **{
                                            ckey: child[ckey]
                                            for ckey in (
                                                "credits",
                                                "label",
                                                "subjectId",
                                            )
                                        },
                                        **{"isStarted": False},
                                    }
                                    for child in entry["children"]
                                    if child.get("subjectId") not in passed_subjects
                                }
                            )
                            for ekey in (
                                "label",
                                "credits",
                                "children",
                                "presupposedModuleIds",
                                "moduleId",
                            )
                        },
                        **{"isEnrolled": False},
                    }
                    for entry in semester.get("children")
                    if entry.get("moduleId") not in passed_modules
                    and not set(entry.get("presupposedModuleIds", [])) - passed_modules
                    or not passed_modules
                }
            }
            for semester in response.json()["curriculumEntries"]
        }
        self.debug("Successfully retrieved curriculum entries")
        return curriculum_entries

    @ExceptionHandler("failed to draw dependency graph", RequestFailed)
    def get_dependency_graph(
        self, *, cached: bool = False, include_root: bool = False
    ) -> nx.Graph:
        """
        Method examines dependencies between curriculum entries and generates a graph in PNG format.

        Keyword arguments:
            cached: bool, default is False,
                if True, response will be retrieved from cache.

            include_root: bool default is False,
                if True, independent curriculum entries will be drawn around a root node.

        Returns:
            networkx.Graph,
                Graph instance.
        """

        self.debug("requested dependecy graph")
        if cached and self.get(f"{self.username}.dependency_graph"):
            return self[f"{self.username}.dependency_graph"]

        # make sure to have valid booking id
        if not self.get(f"{self.username}.booking_id"):
            self.get_booking_id()

        response = partial(
            self._session.get,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/fetchCurriculumEntry",
            params={"bookindId": self.get(f"{self.username}.booking_id")},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        data = response.json()

        self.debug("creating networkx.Graph instance")
        # create graph
        G = nx.DiGraph()
        # add nodes
        for node in [
            {
                "node": re.sub(r"\s?\(", "\n(", course["label"]),
                "weight": len(
                    course["presupposedModuleIds"] + ([""] if include_root else [])
                ),
            }
            for sem in data["curriculumEntries"]
            for course in sem["children"]
            + ([{"node": "", "weight": 1}] if include_root else [])
            if course["presupposedModuleIds"] or include_root
        ]:
            G.add_node(node["node"], weight=node["weight"])
        # add edges
        for edge in [
            {
                "edge": (
                    re.sub(r"\s?\(", "\n(", course["label"]),
                    next(
                        (
                            re.sub(r"\s?\(", "\n(", course2["label"])
                            for sem2 in data["curriculumEntries"]
                            for course2 in sem2["children"]
                            if course2["moduleId"] == module
                        ),
                        "",
                    ),
                ),
                "weight": len(
                    course["presupposedModuleIds"] + ([""] if include_root else [])
                ),
            }
            for sem in data["curriculumEntries"]
            for course in sem["children"]
            for module in course["presupposedModuleIds"]
            + ([""] if include_root else [])
            if course["presupposedModuleIds"] or include_root
        ]:
            G.add_edge(*edge["edge"], weight=edge["weight"])

        self.debug("created: " + str(G))
        self[f"{self.username}.dependency_graph"] = G
        return G

    @ExceptionHandler("failed to create booking context", RequestFailed)
    def create_booking_context(self, curriculum_entries: dict) -> dict:
        """
        Creates sets of keyword parameters required for the methods:
            "enroll",
            "cancel",
            "dispatch"

        Positional arguments:
            curriculum_entries: dict,
                originates with the result of the "get_curricullum_entries" method.

        Returns:
            dict:
            {
                semester: {
                    curriculum entry id: {
                        "label": str
                        "credits": int
                        "children": {
                            id: {
                                "credits": int,
                                "label": str,
                                "subjectId": str,
                                "isStarted": bool,
                                "dispatching_context": {
                                    "enrolmentPeriodId": str,
                                    "lectureSeriesId": str,
                                    "assignedSubjectIds": str,
                                    "curriculumEntryId": str,
                                    "bookingId": str
                                }
                            }
                        },
                        "presupposedModuleIds": [moduleId, ...],
                        "moduleId": str,
                        "isEnrolled": bool,
                        "booking_context": {
                            "enrolmentPeriodId": str,
                            "lectureSeriesId": str,
                            "assignedSubjectIds": str,
                            "curriculumEntryId": str,
                            "bookingId": str
                        }
                    }
                }, ...
            }
        """

        # make sure to have valid booking id
        if not self.get(f"{self.username}.booking_id"):
            self.get_booking_id()

        self.debug("Retrieving lecture series")
        response = partial(
            self._session.get,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/fetchCourses",
            params={"bookindId": self.get(f"{self.username}.booking_id")},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        for course in response.json().values():
            for body in curriculum_entries.values():
                for curriculumEntryId, subject in body["subjects"].items():
                    if course.get("moduleId"):
                        if str(subject["moduleId"]) == str(course.get("moduleId")):
                            subject["booking_context"] = {
                                # https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/BookCourse
                                "enrolmentPeriodId": str(
                                    course["enrolmentPeriodIds"][0]
                                ),
                                "lectureSeriesId": str(
                                    course["lectureSeries"][0]["id"]
                                ),
                                # drop assignedSubjectIds for cancel request:
                                # https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/CancelBooking
                                "assignedSubjectIds": ",".join(
                                    map(
                                        str,
                                        [
                                            child["subjectId"]
                                            for child in subject["children"].values()
                                        ],
                                    )
                                ),
                                "curriculumEntryId": str(curriculumEntryId),
                                "bookingId": str(
                                    self.get(f"{self.username}.booking_id")
                                ),
                            }
                    elif course.get("subjectId"):
                        for child in subject["children"].values():
                            if str(child["subjectId"]) == str(course.get("subjectId")):
                                child["dispatching_context"] = {
                                    "enrolmentPeriodId": str(
                                        course["enrolmentPeriodIds"][0]
                                    ),
                                    "lectureSeriesId": str(
                                        course["lectureSeries"][0]["id"]
                                    ),
                                    "assignedSubjectIds": "",
                                    "curriculumEntryId": str(curriculumEntryId),
                                    "bookingId": str(
                                        self.get(f"{self.username}.booking_id")
                                    ),
                                }
        self.debug("Successfully updated curriculum entries")
        return curriculum_entries

    @ExceptionHandler("failed to update enrolled curriculum entries", RequestFailed)
    def update_enrolled_course_modules(self, curriculum_entries: dict) -> dict:
        """
        Updates "isEnrolled" and "isStarted" attributes of the result set
        originating with the "get_curricullum_entries" method.

        Positional arguments:
            curriculum_entries: dict,
                originates with the result of the "get_curricullum_entries" method.

        Returns:
            dict:
            {
                semester: {
                    curriculum entry id: {
                        "label": str
                        "credits": int
                        "children": {
                            id: {
                                "credits": int,
                                "label": str,
                                "subjectId": str,
                                "isStarted": bool,
                                ...
                            }
                        },
                        "presupposedModuleIds": [moduleId, ...],
                        "moduleId": str,
                        "isEnrolled": bool,
                        ...
                    }
                }, ...
            }
        """

        # make sure to have valid booking id
        if not self.get(f"{self.username}.booking_id"):
            self.get_booking_id()

        self.debug("Retrieving enrolled curriculum entries")
        # get enrolled courses
        response = partial(
            self._session.get,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/fetchCourseTickets",
            params={"bookindId": self.get(f"{self.username}.booking_id")},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        # mark curriculum entries with enrollment
        for enrollment in response.json():
            for body in curriculum_entries.values():
                if enrollment.get("subjectId"):
                    for subject in body["subjects"].values():
                        for child in subject["children"].values():
                            if str(child["subjectId"]) == str(enrollment["subjectId"]):
                                child.update({"isStarted": True})
                                subject.update({"isEnrolled": True})
                else:
                    for curriculumEntryId, subject in body["subjects"].items():
                        if str(curriculumEntryId) == str(
                            enrollment.get("curriculumEntryId")
                        ):
                            subject.update({"isEnrolled": True})
        self.debug("Successfully updated curriculum entries")
        return curriculum_entries

    @ExceptionHandler("failed to retrieve available credits", RequestFailed)
    def get_available_credits(self) -> dict[str, int]:
        """
        Retrieves available credits.

        Returns:
            dict[str,int]:
            {
                "booked": int,
                "total": int,
                "remaining": int,
                "statisticalTotalCredits": int
            }
        """

        # make sure to have valid booking id
        if not self.get(f"{self.username}.booking_id"):
            self.get_booking_id()

        self.debug("Retrieving available credits")
        response = partial(
            self._session.get,
            "https://care-fs.iubh.de/ajax/4713/CourseInscriptionCurricular/DefaultController/fetchCreditCounts",
            params={"bookindId": self.get(f"{self.username}.booking_id")},
        )()
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        self.debug("Successfully retrieved available credits")
        return response.json()

    @ExceptionHandler("failed to obtain available courses", RequestFailed)
    def get_courses_to_register(self, cached: bool = False) -> dict:
        """
        Generates JSON object describing curriculum entires available for registration
        by executing following method chain:

            self.get_booking_id()
            curriculum_entries = self.update_enrolled_course_modules(
                self.create_booking_context(
                    self.get_curricullum_entries(
                        *self.get_graded_records()
                    )
                )
            )

        Keyword arguments:
            cached: bool, default is False,
                if True, response will be retrieved from cache.

        Returns:
            dict:
            {
                "counts": {
                    "booked": int,
                    "total": int,
                    "remaining": int,
                    "statisticalTotalCredits": int
                },
                "semesters": [
                    {
                        "cluster": str,
                        "subjects": [
                            {
                                "name": str,
                                "shortname": str,
                                "credits": int,
                                "isEnrolled": bool,
                                "booking": {
                                    "enrolmentPeriodId": str,
                                    "lectureSeriesId": str,
                                    "assignedSubjectIds": str,
                                    "curriculumEntryId": str,
                                    "bookingId": str
                                },
                                "lectures": [
                                    {
                                        "name": str,
                                        "shortname": str,
                                        "credits": int,
                                        "isStarted": bool,
                                        "dispatching": {
                                            "enrolmentPeriodId": str,
                                            "lectureSeriesId": str,
                                            "assignedSubjectIds": str,
                                            "curriculumEntryId": str,
                                            "bookingId": str
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )
        """
        if cached and self.get(f"{self.username}.curriculum"):
            return self[f"{self.username}.curriculum"]

        curriculum_entries = self.update_enrolled_course_modules(
            self.create_booking_context(
                self.get_curricullum_entries(*self.get_graded_records())
            )
        )
        credits = self.get_available_credits()

        split = re.compile(r"(.*?)\s*\((.*)\)", re.DOTALL)
        result = {
            "counts": credits,
            "semesters": [
                {
                    "cluster": k,
                    "subjects": [
                        {
                            **{
                                "name": (
                                    split.match(subject["label"]).group(1)
                                    if split.match(subject["label"])
                                    else subject["label"]
                                    .replace("\n", " ")
                                    .replace(" " * 2, " ")
                                ),
                                "shortname": (
                                    split.match(subject["label"]).group(2)
                                    if split.match(subject["label"])
                                    else ""
                                ),
                            },
                            "credits": subject["credits"],
                            "isEnrolled": subject["isEnrolled"],
                            "booking": subject.get("booking_context"),
                            "lectures": [
                                {
                                    **{
                                        "name": (
                                            split.match(child["label"]).group(1)
                                            if split.match(child["label"])
                                            else child["label"]
                                            .replace("\n", " ")
                                            .replace(" " * 2, " ")
                                        ),
                                        "shortname": (
                                            split.match(child["label"]).group(2)
                                            if split.match(child["label"])
                                            else ""
                                        ),
                                    },
                                    "credits": child["credits"],
                                    "isStarted": child["isStarted"],
                                    "dispatching": child.get("dispatching_context"),
                                }
                                for child in subject["children"].values()
                            ],
                        }
                        for subject in v["subjects"].values()
                    ],
                }
                for k, v in curriculum_entries.items()
            ],
        }
        self[f"{self.username}.curriculum"] = result
        return result


if __name__ == "__main__":
    with CourseBrowser(
        input("username: "),
        input("password: "),
        max_len=100,
        max_age=30,
        filepath=__file__,
        verbose=True,
    ) as handler:
        handler.sign_in()
        print(handler.get_booking_id())
        print(handler.get_curricullum_entries(set(), set()))
        # print(*handler.list_courses(), sep='\n')
        # print(*handler.list_course_resources(1902), sep='\n')
        # import json
        # print(json.dumps(handler.get_courses_to_register(cached=False), indent=4))
        # print(handler.get_dependency_graph(cached=False))
