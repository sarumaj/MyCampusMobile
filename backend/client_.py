# -*- coding: utf-8 -*-

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

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

from .auth import ContextManager
from .cache import Cache
from .dumper import dump4mock

###############
#             #
# definitions #
#             #
###############


class Client_(ContextManager, Cache):
    """
    Mock instance for the client.Client
    """

    def __init__(self, *args, **kwargs):
        ContextManager.__init__(self)
        temp_dir = tempfile.mkdtemp()
        Cache.__init__(
            self,
            filename=Path(temp_dir).name,
            filepath=temp_dir,
            verbose=True,
            max_age=60**2,
            max_len=100,
        )

    # Authenticator
    get_saml_request = MagicMock(
        return_value=dump4mock["Authenticator.get_saml_request.SAMLrequest#1"]
    )
    get_saml_response = MagicMock(
        return_value=dump4mock["Authenticator.get_saml_response.SAMLresponse#1"]
    )
    submit_saml_response = MagicMock(return_value=None)
    close = MagicMock(return_value=None)

    # CalendarExporter
    export_calendar = MagicMock(
        return_value=(
            dump4mock["CalendarExporter.export_calendar.fname#1"],
            dump4mock["CalendarExporter.export_calendar.result#1"],
        )
    )

    # Downloader
    # not possible to mock iter_content behavior
    download = MagicMock(
        return_value=(
            dump4mock["Downloader.download.content_disposition#1"],
            dump4mock["Downloader.download.response.content@session.get(link)#1"],
            dump4mock["Downloader.download.content_length#1"],
        )
    )

    # GradesReporter
    get_grades = MagicMock(return_value=dump4mock["GradesReporter.get_grades.result#1"])

    # CourseBrowser
    list_courses = MagicMock(
        return_value=dump4mock("CourseBrowser.list_courses.result#1")
    )
    list_course_resources = MagicMock(
        side_effect=lambda course_id: {
            course["id"]: dump4mock(
                "CourseBrowser.list_course_resources.result[%d]#1" % course["id"]
            )
            for course in dump4mock("CourseBrowser.list_courses.result#1")
        }[course_id]
    )


if __name__ == "__main__":
    with Client_(True, "hi") as mock:
        print(mock.list_course_resources(2639))
