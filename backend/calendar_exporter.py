# -*- coding: utf-8 -*-

import sys
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from bs4 import BeautifulSoup
from icalendar import Calendar

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
from .dumper import dump4mock
from .exceptions import ExceptionHandler, RequestFailed

###############
#             #
# definitions #
#             #
###############


class ExportEvents(Enum):
    """
    Parameters provided by the PHP endpoint at MyCampus.
    """

    all = 0
    categories = 1
    courses = 2
    groups = 3
    user = 4


class TimePeriod(Enum):
    """
    Parameters provided by the PHP endpoint at MyCampus.
    """

    weeknow = 0
    weeknext = 1
    monthnow = 2
    recentupcoming = 3
    custom = 4


class CalendarExporter(Authenticator):
    """
    Implements method to export student's calendar in "ical" format.
    """

    @ExceptionHandler("calendar export failed", RequestFailed)
    def export_calendar(
        self,
        *,
        exportevents: ExportEvents = ExportEvents["all"],
        timeperiod: TimePeriod = TimePeriod["recentupcoming"],
        cached: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        """
        Sends request to the corresponding PHP endpoint to export calendar events in the "ical" format.

        Keyword arguments:
            exportevents: ExportEvents, default is "all",
                parameter used by the PHP endpoint.

            timeperiod: TimePeriod, default is "recentupcoming"
                parameter used by the PHP endpoint.

            cached: bool, default is False,
                if True, response will be retrieved from cache.

        Returns:
            dict:
                {
                    "ical": str
                    "parsed": [{
                        "summary": bytes,
                        "description": bytes,
                        "dtstart": datetime.datetime,
                        "dtend": datetime.datetime,
                        "location": bytes
                    }, ...]
                }
        """

        fname = f"ical_events({exportevents.name})_period({timeperiod.name}).ics"
        if cached and self.get(f"{self.username}.{fname}") is not None:
            return fname, self[f"{self.username}.{fname}"]

        # send HTTP request to PHP endpoint
        self.debug("Requesting calendar export context")
        response = self._session.get("https://mycampus.iubh.de/calendar/export.php")
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.get(%s)"
            % quote("https://mycampus.iubh.de/calendar/export.php", safe="")
        )
        self.debug("Successfully retrieved export options")

        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.select_one("form", class_="mform")
        fields = {
            "export": "Export",
            **{
                el.get("name"): el.get("value")
                for el in soup.select('input[type="hidden"]')
            },
        }
        # store calendar options for lookup
        self[f"{self.username}.calendar_options"] = {
            "exportevents": [
                el.get("value")
                for el in soup.select('input[name="events[exportevents]"]')
            ],
            "timeperiod": [
                el.get("value")
                for el in soup.select('input[name="period[timeperiod]"]')
            ],
        }
        form = urlencode(
            {
                **fields,
                **{
                    "events[exportevents]": {
                        el: el
                        for el in self[f"{self.username}.calendar_options"][
                            "exportevents"
                        ]
                    }.get(exportevents.name, "all"),
                    "period[timeperiod]": {
                        el: el
                        for el in self[f"{self.username}.calendar_options"][
                            "timeperiod"
                        ]
                    }.get(timeperiod.name, "recentupcoming"),
                },
            }
        )

        self.debug("Exporting calendar events")
        response = self._session.post(
            "https://mycampus.iubh.de/calendar/export.php",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=form,
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.post(%s,data=form)"
            % quote("https://mycampus.iubh.de/calendar/export.php", safe="")
        )

        cal = Calendar.from_ical(response.text)
        result = {
            "ical": response.text,
            "parsed": [
                {
                    key: event.decoded(key) if event.get(key) else None
                    for key in (
                        "summary",
                        "description",
                        "dtstart",
                        "dtend",
                        "location",
                    )
                }
                for event in cal.walk("vevent")
            ],
        }
        dump4mock("fname")
        dump4mock("result")
        self[f"{self.username}.{fname}"] = result
        self.debug("Successfully exported calendar events")
        return fname, result


if __name__ == "__main__":
    with CalendarExporter(
        input("username: "),
        input("password: "),
        max_len=100,
        max_age=30,
        filepath=__file__,
        verbose=True,
    ) as handler:
        dump4mock([CalendarExporter.__name__, Authenticator.__name__])
        handler.sign_in()
        print(handler.export_calendar())
