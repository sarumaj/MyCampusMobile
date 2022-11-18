# -*- coding: utf-8 -*-

from backend.auth import Authenticator
from backend.calendar_exporter import CalendarExporter
from backend.course_browser import CourseBrowser
from backend.downloader import Downloader
from backend.dumper import dump4mock
from backend.grades_reporter import GradesReporter


def dump_auth():
    global username
    global password
    with Authenticator(
        username,
        password,
        max_len=100,
        max_age=30,
        filepath=__file__,
        verbose=True,
    ) as handler:
        handler.sign_in()


def dump_calendar_exporter():
    global username
    global password
    with CalendarExporter(
        username,
        password,
        max_len=100,
        max_age=30,
        filepath=__file__,
        verbose=True,
    ) as handler:
        handler.sign_in()
        handler.export_calendar()


def dump_course_browser():
    global username
    global password
    with CourseBrowser(
        username,
        password,
        max_len=100,
        max_age=30,
        filepath=__file__,
        verbose=True,
    ) as handler:
        handler.sign_in()
        for course in handler.list_courses():
            handler.list_course_resources(int(course["id"]))
        handler.get_booking_id()
        passed_modules, passed_subjects = handler.get_graded_records()
        entries = handler.get_curricullum_entries(set(), set())
        entries = handler.create_booking_context(entries)
        handler.update_enrolled_course_modules(entries)
        entries = handler.get_curricullum_entries(passed_modules, passed_subjects)
        entries = handler.create_booking_context(entries)
        handler.update_enrolled_course_modules(entries)
        handler.get_dependency_graph()
        handler.get_available_credits()
        handler.get_courses_to_register()


def dump_downloader():
    global username
    global password
    handler = Downloader(
        username,
        password,
        max_len=100,
        max_age=30,
        filepath=__file__,
        verbose=True,
    )
    handler.download("https://www.example.com")


def dump_grades_reporter():
    global username
    global password
    with GradesReporter(
        username,
        password,
        max_len=100,
        max_age=10,
        filepath=__file__,
        verbose=True,
    ) as handler:
        handler.sign_in()
        handler.get_grades()


if __name__ == "__main__":
    username = input("enter your username, please: ")
    password = input("enter your password, please: ")
    dump4mock.DUMP_CLASS = [
        Authenticator,
        CalendarExporter,
        CourseBrowser,
        Downloader,
        GradesReporter,
    ]
    dump4mock(dump4mock.DUMP_CLASS)
    dump_auth()
    dump_calendar_exporter()
    dump_course_browser()
    dump_downloader()
    dump_grades_reporter()
