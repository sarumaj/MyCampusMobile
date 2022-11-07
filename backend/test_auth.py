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

from .auth import Authenticator
from .dumper import MockDumper

AUTHENTICATOR = Authenticator(
    "username",
    "password",
    max_len=100,
    max_age=30,
    filepath=tempfile.gettempdir(),
    verbose=True,
)


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        self.auth = AUTHENTICATOR

    @patch("__main__.AUTHENTICATOR._session")
    def test_get_saml_request(self, session_mock):
        session_mock.get.return_value = MagicMock(
            status_code=200,
            text=MockDumper.read("Authenticator.get_saml_request.response.text#1.dump"),
        )
        self.assertEqual(
            self.auth.get_saml_request(),
            MockDumper.read("Authenticator.get_saml_request.SAMLrequest#1.dump"),
        )

    @patch("__main__.AUTHENTICATOR._session")
    def test_get_saml_response(self, session_mock):
        session_mock.post.side_effect = (
            MagicMock(
                status_code=200,
                text=MockDumper.read(
                    "Authenticator.get_saml_response.response.text#1.dump"
                ),
            ),
            MagicMock(
                status_code=200,
                text=MockDumper.read(
                    "Authenticator.get_saml_response.response.text#2.dump"
                ),
            ),
        )
        self.assertEqual(
            self.auth.get_saml_response(
                MockDumper.read("Authenticator.get_saml_request.SAMLrequest#1.dump")
            ),
            MockDumper.read("Authenticator.get_saml_response.SAMLresponse#1.dump"),
        )

    @patch("__main__.AUTHENTICATOR._session")
    def test_submit_saml_response(self, session_mock):
        session_mock.post.return_value = MagicMock(
            status_code=200,
            text=MockDumper.read(
                "Authenticator.submit_saml_response.response.text#1.dump"
            ),
        )
        self.assertEqual(
            self.auth.submit_saml_response(
                MockDumper.read("Authenticator.get_saml_response.SAMLresponse#1.dump")
            ),
            None,
        )

    @patch("__main__.AUTHENTICATOR._session")
    def test_sign_out(self, session_mock):
        session_mock.get.side_effect = (
            MagicMock(
                status_code=200,
                text=MockDumper.read("Authenticator.close.response.text#1.dump"),
            ),
            MagicMock(
                status_code=200,
                text=MockDumper.read("Authenticator.close.response.text#2.dump"),
            ),
        )
        self.assertEqual(self.auth.close(), None)


if __name__ == "__main__":
    unittest.main()
