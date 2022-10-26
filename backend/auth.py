# -*- coding: utf-8 -*-
 
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import re
from typing import TextIO, Optional

####################################
#                                  #
# preamble to provide package name #
#                                  #
####################################

import sys
from pathlib import Path

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[1]
    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError:
        pass
    __package__ = '.'.join(parent.parts[len(top.parts):])

from .exceptions import *
from .cache import Cache

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
                self.close()
            except:
                self.warning("Sign-out failed")
            if exception:
                self.debug(f'Shutting down gracefully. Reason: {exception.__name__}("{content}")')
        return True

    def close(self):
        """To do: implement in the parent class"""

class Authenticator(Cache, ContextManager):
    """
    Abstraction level handling the authentication and authorization schema to access MyCampus.
    """

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, value:str):
        self.__username = value
        # cache username
        self['username'] = value
        self[value] = dict()

    @property
    def password(self) -> str:
        return NotImplementedError

    @password.setter
    def password(self, value:str):
        self.__password = value

    def __init__(self, 
        username:str, 
        password:str, 
        *streams: tuple[TextIO], 
        filepath: str, 
        filename: Optional[str] = 'app.log',
        emit: Optional[bool] = True,
        verbose: Optional[bool] = False, 
        max_len:int, 
        max_age:int, 
        items: Optional[dict]=None
    ):
        """
        Initliazes internal cache. Can be used as context manager.
        """

        ContextManager.__init__(self)
        Cache.__init__(
            self, *streams, 
            filepath=filepath, filename=filename, emit=emit,
            verbose=verbose, max_len=max_len, max_age=max_age,
            items=items
        )
        # start a cookie based session
        self._session = requests.Session()
              
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

        self.submit_saml_response(
            self.get_saml_response(
                self.get_saml_request()
            )
        )
        self.debug("Successfully signed in")

    @ExceptionHandler("mycamupus.iubh.de was not reachable", SignInFailed)
    def get_saml_request(self) -> str:
        self.debug("Retrieving SAML request")
        # initialize session with response from mycampus
        response = self._session.get("https://mycampus.iubh.de/my/")
        assert response.status_code == 200, "server responded with %d (%s)" % (response.status_code, response.text)
        # scrap SAML request for authentication
        soup = BeautifulSoup(response.text, 'html.parser')
        SAMLrequest = urlencode(
            {
                el.get('name'):el.get('value') for el in soup.select('input[type="hidden"]')
            }
        )
        self.debug("Successfully retrieved SAML request")
        return SAMLrequest

    
    @ExceptionHandler("failed to retrieve SAML response", SignInFailed)
    def get_saml_response(self, SAMLrequest:str) -> str: 
        self.debug("Submitting SAML request")
        response = self._session.post(
            "https://login.iubh.de/idp/profile/SAML2/POST/SSO", 
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=SAMLrequest
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (response.status_code, response.text)

        # scrap hidden login form input fields
        soup = BeautifulSoup(response.text, 'html.parser')
        querystring = dict(
            re.findall(
                '(?:\?|\&)(?:([^&]*?)(?:\=)([^&]*))', 
                soup.find('form', id='login').get('action')
            )
        )
        form = urlencode(
            {
                'j_username': self.__username,
                'j_password': self.__password,
                '_eventId_proceed': '',
                **{
                    el.get('name'):el.get('value') for el in soup.select('input[type="hidden"]')
                }
            }
        )
        self.debug("Submitting sign-in form")
        response = self._session.post(
            "https://login.iubh.de/idp/profile/SAML2/POST/SSO", 
            params=querystring,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=form
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (response.status_code, response.text)

        # scrap SAML response
        soup = BeautifulSoup(response.text, 'html.parser')
        SAMLresponse = urlencode(
            {
                el.get('name'):el.get('value') for el in soup.select('input[type="hidden"]')
            }
        )
        self.debug("Successfully set up SAML response")
        return SAMLresponse

    @ExceptionHandler("failed to submit SAML request", SignInFailed)
    def submit_saml_response(self, SAMLresponse:str):
        self.debug("Submitting SAML response")
        response = self._session.post(
            "https://mycampus.iubh.de/auth/saml2/sp/saml2-acs.php/mycampus.iubh.de", 
            headers={'Content-Type': 'application/x-www-form-urlencoded'}, 
            data=SAMLresponse
        )
        assert response.status_code == 200, "server responded with %d (%s)" % (response.status_code, response.text)
        self.debug("Successfully submitted SAML response")

    @ExceptionHandler("sign-out request failed", SignOutFailed)
    def close(self):
        """
        Sends sign-out request.
        """
        # scrap logout endpoint to submit a sign-out request
        self.debug("Signing out")
        response = self._session.get("https://mycampus.iubh.de/my/")
        soup = BeautifulSoup(response.text, 'html.parser')
        logout = soup.select_one('a[href^="https://mycampus.iubh.de/login/logout.php"]').get('href')
        response = self._session.get(logout)
        assert response.status_code == 200, "server responded with %d (%s)" % (response.status_code, response.text)
        self.debug("Successfully signed out")

if __name__ == '__main__':
    with Authenticator(
        input('username: '), 
        input('password: '),
        max_len=100,
        max_age=30,
        filepath=__file__,
        verbose=True
    ) as handler:
        handler.sign_in()