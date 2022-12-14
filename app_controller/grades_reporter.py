# -*- coding: utf-8 -*-

import re
from collections import OrderedDict
from urllib.parse import quote

from bs4 import BeautifulSoup

from .auth import Authenticator
from .dumper import dump4mock
from .exceptions import ExceptionHandler, RequestFailed

###############
#             #
# definitions #
#             #
###############


class GradesReporter(Authenticator):
    """
    Implements methods to retrieve student's grades.
    """

    @ExceptionHandler("could not retrieve data", RequestFailed)
    def get_grades(self, cached: bool = False) -> OrderedDict:
        """
        Returns grades with legend.

        Keyword arguments:
            cached: bool, default is False,
                if True, response will be retrieved from cache.

        Returns:
            dict:
            {
                <semester>: {
                    "ID": str,
                    "Module / Course": str,
                    "Status": str,
                    "Grade": float,
                    "Rating": float,
                    "Credits": int,
                    "Try": int,
                    "Date": str,
                    "Type of course": str,
                    "Comment": str,
                    "Recognition": str
                }
            }

        """

        if cached and self.get(f"{self.username}.grades") is not None:
            return self[f"{self.username}.grades"]

        # call PHP endpoint
        self.debug("Requesting legend object")
        response = self._session.get(
            "https://mycampus.iubh.de/local/iubh_ac5sso/ac5notenuebersicht.php"
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.get(%s)"
            % quote(
                "https://mycampus.iubh.de/local/iubh_ac5sso/ac5notenuebersicht.php",
                safe="",
            ),
            True,
        )
        soup = BeautifulSoup(response.text, "html.parser")
        # load iframe content
        url = soup.select_one("iframe", id="ac5frame").get("src")
        response = self._session.get(url)
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock("response.text@session.get(url)", True)
        self.debug("Successfully retrieved legend object")

        self.debug("Requesting grades table object")
        response = self._session.get(
            "https://care-fs.iubh.de/en/examinations/examination-results.php"
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.get(%s)"
            % quote(
                "https://care-fs.iubh.de/en/examinations/examination-results.php",
                safe="",
            ),
            True,
        )
        soup = BeautifulSoup(response.text, "html.parser")
        # retrieve legend from HTML table object
        legend = [
            td.text
            for td in soup.select_one('table[class="table table-striped"]').find_all(
                "td"
            )
        ]
        legend = {
            legend[i : i + 2][0]
            .strip("\n"): legend[i : i + 2][1]
            .split("|")[0]
            .strip()
            .title()
            for i in range(0, len(legend), 2)
        }
        regex = re.compile("|".join(map(re.escape, legend.keys())))
        semesters = soup.find_all("div", class_="panel panel-default")
        result = OrderedDict()
        # iterate over semesters
        for semester in semesters:
            semester_div = semester.select_one('div[class="panel-heading"]')
            if semester_div is not None:
                head = [td.text for td in semester.select_one("thead").find_all("td")]
                body = [td.text for td in semester.select_one("tbody").find_all("td")]
                # map table headers to rows
                grades = list(
                    filter(
                        # get only subject lectures
                        lambda x: re.match(r"^\w+0[1-9]$", x.get("ID", "")),
                        [
                            dict(zip(head, body[i : i + len(head)]))
                            for i in range(0, len(body), len(head))
                        ],
                    )
                )

                if grades:
                    result[semester_div.text] = [
                        {
                            k: (
                                regex.sub(
                                    lambda mo: legend[mo.string[mo.start() : mo.end()]],
                                    v.strip("\n"),
                                )
                                if k == "Status"
                                else (float(v.replace(",", ".")) if v != "" else 0.0)
                                if k == "Grade"
                                else (
                                    float(v.split("/")[0].strip()) / 100
                                    if v != ""
                                    else 0.0
                                )
                                if k == "Rating"
                                else (int(v.split("/")[0].strip()) if v != "" else 0)
                                if k == "Credits"
                                else (int(v) if v.isdigit() else 0)
                                if k == "Try"
                                else v
                            )
                            for k, v in gr.items()
                        }
                        for gr in grades
                    ]
        dump4mock("result", True)
        self[f"{self.username}.grades"] = result
        self.debug("Successfully retrieved grades")
        return result
