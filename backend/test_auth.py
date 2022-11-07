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

MOCK_DIR = Path(__file__).parent / "mock"
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
        response = MagicMock(status_code=200)
        with open(MOCK_DIR / "auth.get_saml_request.reponse.text.dump", "r") as f:
            response.text = f.read()
        session_mock.get.return_value = response

        with open(MOCK_DIR / "saml_request.dump") as f:
            self.assertEqual(self.auth.get_saml_request(), f.read())

    @patch("__main__.AUTHENTICATOR._session")
    def test_get_saml_response(self, session_mock):
        response = MagicMock(status_code=200)
        with open(MOCK_DIR / "auth.get_saml_response#1.reponse.text.dump", "r") as f:
            response.text = f.read()

        response2 = MagicMock(status_code=200)
        with open(MOCK_DIR / "auth.get_saml_response#2.reponse.text.dump", "r") as f:
            response2.text = f.read()

        session_mock.post.side_effect = (response, response2)

        with open(MOCK_DIR / "saml_response.dump") as f, open(
            MOCK_DIR / "saml_request.dump"
        ) as f2:
            self.assertEqual(self.auth.get_saml_response(f2.read()), f.read())


if __name__ == "__main__":
    unittest.main()
