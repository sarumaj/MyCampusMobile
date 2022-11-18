# -*- coding: utf-8 -*-

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.downloader import Downloader
from backend.dumper import dump4mock


class DownloaderTestCase(unittest.TestCase):
    client = Downloader(
        "username",
        "password",
        max_len=100,
        max_age=30,
        filepath=tempfile.gettempdir(),
        verbose=False,
        emit=False,
    )

    @patch.object(client, "_session")
    def test_download(self, session_mock):
        session_mock.get.return_value = MagicMock(
            status_code=200,
            text=dump4mock["Downloader.download.response.text@session.get(link)#1"],
            headers=dump4mock[
                "Downloader.download.response.headers@session.get(link)#1"
            ],
            content=dump4mock[
                "Downloader.download.response.content@session.get(link)#1"
            ],
        )

        self.assertEqual(
            self.client.download("https://www.example.com"),
            (
                dump4mock["Downloader.download.content_disposition#1"],
                dump4mock["Downloader.download.response.content@session.get(link)#1"],
                dump4mock["Downloader.download.content_length#1"],
            ),
        )

    def test_save(self):
        dir = Path(tempfile.mkdtemp())
        location = self.client.save(
            dump4mock["Downloader.download.content_disposition#1"],
            dump4mock["Downloader.download.response.content@session.get(link)#1"],
            dir,
        )
        self.assertEqual(
            location.name, dump4mock["Downloader.download.content_disposition#1"]
        )
        location = self.client.save(
            dump4mock["Downloader.download.content_disposition#1"],
            dump4mock["Downloader.download.response.content@session.get(link)#1"],
            dir,
        )
        self.assertEqual(
            location.name,
            "%s (1)" % dump4mock["Downloader.download.content_disposition#1"],
        )
