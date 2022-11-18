# -*- coding: utf-8 -*-

import tempfile
import unittest
from unittest.mock import MagicMock, patch

from backend.auth import Authenticator
from backend.dumper import dump4mock


class AuthenticatorTestCase(unittest.TestCase):
    auth = Authenticator(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=False,
        emit=False,
    )

    @patch.object(auth, "_session")
    def test_get_saml_request(self, session_mock):
        session_mock.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "Authenticator.get_saml_request.response.text"
                "@session.get(https%3A%2F%2Fmycampus.iubh.de%2Fmy)#1"
            ],
        )
        self.assertEqual(
            self.auth.get_saml_request(),
            dump4mock["Authenticator.get_saml_request.SAMLrequest#1"],
        )

    @patch.object(auth, "_session")
    @patch.object(auth, "get_saml_request")
    def test_get_saml_response(self, get_saml_request, session_mock):
        get_saml_request.return_value = dump4mock[
            "Authenticator.get_saml_request.SAMLrequest#1"
        ]
        session_mock.post.side_effect = (
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
        self.assertEqual(
            self.auth.get_saml_response(self.auth.get_saml_request()),
            dump4mock["Authenticator.get_saml_response.SAMLresponse#1"],
        )
        get_saml_request.assert_called_with()

    @patch.object(auth, "_session")
    @patch.object(auth, "get_saml_response")
    def test_submit_saml_response(self, get_saml_response, session_mock):
        get_saml_response.return_value = dump4mock(
            "Authenticator.get_saml_response.SAMLresponse#1"
        )
        session_mock.post.return_value = MagicMock(
            status_code=200,
            text=dump4mock[
                "Authenticator.submit_saml_response.response.text"
                "@session.post(https%3A%2F%2Fmycampus.iubh.de%2Fauth%2Fsaml2%2Fsp%2Fsaml2-acs.php%2Fmycampus.iubh.de,"
                "data=SAMLresponse)#1"
            ],
        )
        self.assertEqual(
            self.auth.submit_saml_response(self.auth.get_saml_response("SAML request")),
            None,
        )
        get_saml_response.assert_called_with("SAML request")

    @patch.object(auth, "_session")
    def test_sign_out(self, session_mock):
        session_mock.get.side_effect = (
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
        self.assertEqual(self.auth.close(), None)
