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

from .downloader import Downloader
from .dumper import dump4mock


class DownloaderTestCase(unittest.TestCase):
    client = Downloader(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=True,
    )

    @patch.object(client, "_session")
    def test_download(self, session_mock):
        session_mock.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock["Downloader.download.response.text#1"],
            headers=dump4mock["Downloader.download.response.headers#1"],
            content=dump4mock["Downloader.download.response.content#1"],
        )

        self.assertEqual(
            self.client.download("https://www.example.com"),
            (
                dump4mock["Downloader.download.content_disposition#1"],
                dump4mock["Downloader.download.response.content#1"],
                dump4mock["Downloader.download.content_length#1"],
            ),
        )

    def test_save(self):
        dir = Path(tempfile.mkdtemp())
        location = self.client.save(
            dump4mock["Downloader.download.content_disposition#1"],
            dump4mock["Downloader.download.response.content#1"],
            dir,
        )
        self.assertEqual(
            location.name, dump4mock["Downloader.download.content_disposition#1"]
        )
        location = self.client.save(
            dump4mock["Downloader.download.content_disposition#1"],
            dump4mock["Downloader.download.response.content#1"],
            dir,
        )
        self.assertEqual(
            location.name,
            "%s (1)" % dump4mock["Downloader.download.content_disposition#1"],
        )


if __name__ == "__main__":
    unittest.main()
