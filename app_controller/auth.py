# -*- coding: utf-8 -*-

import re
from typing import Optional, TextIO
from urllib.parse import quote, urlencode

import requests
from bs4 import BeautifulSoup

from .cache import Cache
from .dumper import dump4mock
from .exceptions import ExceptionHandler, SignInFailed, SignOutFailed

###############
#             #
# definitions #
#             #
###############


class ContextManager:
    """
    Extentions enabling usage es context manager (with ...).
    """

    def __enter__(self):
        return self

    def __exit__(self, exception, content, traceback) -> bool:
        if isinstance(self, Cache):
            try:
                hasattr(self, "close") and self.close()
            except BaseException:
                self.warning("Sign-out failed")
            if exception:
                self.debug(
                    f'Shutting down gracefully. Reason: {exception.__name__}("{content}")'
                )
        return True


class Authenticator(Cache, ContextManager):
    """
    Abstraction level handling the authentication and authorization schema to access MyCampus.
    """

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        self._username = value
        # cache username
        self["username"] = value
        self.prolongate("username", 365 * 24 * 3600)

    @property
    def password(self) -> str:
        return NotImplementedError

    @password.setter
    def password(self, value: str):
        self._password = value

    def __init__(
        self,
        username: str,
        password: str,
        *streams: tuple[TextIO],
        filepath: str,
        filename: Optional[str] = "app.log",
        emit: Optional[bool] = True,
        verbose: Optional[bool] = False,
        max_len: int,
        max_age: int,
        items: Optional[dict] = None,
        destination: Optional[str] = None,
    ):
        """
        Initliazes internal cache. Can be used as context manager.

        Positional arguments:
            streams : <see type hint>
                a tuple of file like objects.

        Keyword arguments:
            filepath : str or None
                a Windows or POSIX path string.

            filename : str, optional, default is 'app.log'
                name of the log file,
                if None no log file is being created.

            filename : str or None, optional, default is 'app.log'
                name of a log file, if not None,
                log file handler is being created.

            emit : bool, optional, default is True
                if True, DEBUG or INFO and above log
                level messages will be emitted to 'sys.stdout',
                ERROR and CRITICAL to 'sys.stderr';
                emit behavior cannot be disabled if
                no log file handler has been created.

            verbose: bool, optional, default is False
                if True, DEBUG log level will be set
                for both file handler and 'sys.stdout',
                otherwise INFO log level will be set.

            user: str, optional, default is current logon name
                username appearing in the logs.

            max_age: int,
                TTL for records to cache in seconds.

            max_len: int,
                maximum number of records to be held in the cache.
        """

        ContextManager.__init__(self)
        Cache.__init__(
            self,
            *streams,
            filepath=filepath,
            filename=filename,
            emit=emit,
            verbose=verbose,
            max_len=max_len,
            max_age=max_age,
            items=items,
            destination=destination,
        )
        # start a cookie based session
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.28"
                )
            }
        )

        if username:
            self.username = username
        if password:
            self.password = password

    def sign_in(self):
        """
        Performs sign-in by following SAML authentication schema:

            self.submit_saml_response(
                self.get_saml_response(
                    self.get_saml_request()
                )
            )
        """
        self.submit_saml_response(self.get_saml_response(self.get_saml_request()))
        self.debug("Successfully signed in")

    @ExceptionHandler("mycamupus.iubh.de was not reachable", SignInFailed)
    def get_saml_request(self) -> str:
        """
        Method to fetch saml request.

        Returns:
            str
        """

        self.debug("Retrieving SAML request")
        # initialize session with response from mycampus
        response = self._session.get("https://mycampus.iubh.de/my")
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.get(%s)"
            % quote("https://mycampus.iubh.de/my", safe=""),
            True,
        )
        # scrap SAML request for authentication
        soup = BeautifulSoup(response.text, "html.parser")
        SAMLrequest = urlencode(
            {
                el.get("name"): el.get("value")
                for el in soup.select('input[type="hidden"]')
            }
        )
        self.debug("Successfully retrieved SAML request")
        dump4mock("SAMLrequest", True)
        return SAMLrequest

    @ExceptionHandler("failed to retrieve SAML response", SignInFailed)
    def get_saml_response(self, SAMLrequest: str) -> str:
        """
        Method to request SAML response by providing the SAML request challenge.

        Positional arguments:
            SAMLrequest: str,
                SAML request challenge object.

        Returns:
            str
        """

        self.debug("Submitting SAML request")
        response = self._session.post(
            "https://login.iubh.de/idp/profile/SAML2/POST/SSO",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=SAMLrequest,
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.post(%s,data=SAMLrequest)"
            % quote("https://login.iubh.de/idp/profile/SAML2/POST/SSO", safe=""),
            True,
        )

        # scrap hidden login form input fields
        soup = BeautifulSoup(response.text, "html.parser")
        querystring = dict(
            re.findall(
                r"(?:\?|\&)(?:([^&]*?)(?:\=)([^&]*))",
                soup.find("form", id="login").get("action"),
            )
        )
        form = urlencode(
            {
                "j_username": self._username,
                "j_password": self._password,
                "_eventId_proceed": "",
                **{
                    el.get("name"): el.get("value")
                    for el in soup.select('input[type="hidden"]')
                },
            }
        )
        self.debug("Submitting sign-in form")
        response = self._session.post(
            "https://login.iubh.de/idp/profile/SAML2/POST/SSO",
            params=querystring,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=form,
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.post(%s,data=form)"
            % quote("https://login.iubh.de/idp/profile/SAML2/POST/SSO", safe=""),
            True,
        )

        # scrap SAML response
        soup = BeautifulSoup(response.text, "html.parser")
        SAMLresponse = urlencode(
            {
                el.get("name"): el.get("value")
                for el in soup.select('input[type="hidden"]')
            }
        )
        self.debug("Successfully set up SAML response")
        dump4mock("SAMLresponse", True)
        return SAMLresponse

    @ExceptionHandler("failed to submit SAML request", SignInFailed)
    def submit_saml_response(self, SAMLresponse: str):
        """
        Method for submitting SAML response.

        Positional arguments:
            SAMLresponse: str,
                SAML response challenge object.
        """

        self.debug("Submitting SAML response")
        response = self._session.post(
            "https://mycampus.iubh.de/auth/saml2/sp/saml2-acs.php/mycampus.iubh.de",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=SAMLresponse,
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock(
            "response.text@session.post(%s,data=SAMLresponse)"
            % quote(
                "https://mycampus.iubh.de/auth/saml2/sp/saml2-acs.php/mycampus.iubh.de",
                safe="",
            ),
            True,
        )
        self.debug("Successfully submitted SAML response")

    @ExceptionHandler("sign-out request failed", SignOutFailed)
    def close(self):
        """
        Sends sign-out request.
        """

        # scrap logout endpoint to submit a sign-out request
        self.debug("Signing out")
        response = self._session.get("https://mycampus.iubh.de/my/")
        dump4mock(
            "response.text@session.get(%s)"
            % quote("https://mycampus.iubh.de/my/", safe=""),
            True,
        )
        soup = BeautifulSoup(response.text, "html.parser")
        logout = soup.select_one(
            'a[href^="https://mycampus.iubh.de/login/logout.php"]'
        ).get("href")
        response = self._session.get(logout)
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock("response.text@session.get(logout)", True)
        self.debug("Successfully signed out")

    def __del__(self):
        """
        Tear-down for garbage collector
        """

        # self._session.close()
        Cache.__del__(self)
