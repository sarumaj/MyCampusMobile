# -*- coding: utf-8 -*-

import base64
import re
from pathlib import Path
from typing import Generator, Optional, Union

from .auth import Authenticator
from .dumper import dump4mock
from .exceptions import ExceptionHandler, RequestFailed

###############
#             #
# definitions #
#             #
###############


class Downloader(Authenticator):
    """
    Implements methods to download course materials.
    """

    @ExceptionHandler("could not save specified content", RequestFailed)
    def save(
        self,
        filename: str,
        content: Union[bytes, str],
        destination: Optional[Path] = None,
    ) -> Path:
        """
        Saves contents into a local file.

        Keyword arguments:
            filename: str,
                name of the file.

            content: Union[bytes,str],
                content of the file.

            destination: Paht, default is the "Downloads" folder in the home directory,
                location at which the file should be stored.

        Returns:
            Path:
                path to the file including its name.
        """

        if destination is not None and destination.exists():
            target = destination / filename
        else:
            # default download directory
            downloads_path = Path.home() / "Downloads"
            # make if not exists
            if not downloads_path.exists():
                downloads_path.mkdir()
            target = downloads_path / filename
        # check if target file exists
        counter = len(list(target.parent.glob(target.stem + "*")))
        # rename target file to resolve conflict
        if counter > 0:
            while target.exists():
                target = target.parent / f"{target.stem} ({counter}){target.suffix}"
                counter += 1
        # save file contents
        self.debug(f"Saving to {str(target)}")
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        # return path object
        return target

    @ExceptionHandler("could not download specified content", RequestFailed)
    def download(
        self, link: str, cached: Optional[bool] = False, chunk: Optional[int] = None
    ) -> tuple[str, Union[bytes, Generator[bytes, None, None]], int]:
        """
        Sends HTTP request to fetch target file.

        Keyword arguments:
            link: str,
                URI to send the HTTP request to.

            cached: bool, default is False,
                if True, response will be retrieved from cache.

            chunk: int, default is None,
                if set to valid integer, denotes the chunk size in bytes.

        Returns:
            tuple[str,Union[bytes,Generator[bytes,None,None]],int]:
                From left to right:
                    content-disposition,
                    content,
                    content-lenght.
        """

        cache_key = f"{self.username}.link({base64.b64encode(link.encode('utf-8')).decode('utf-8')})"
        if all(
            (
                cached and self.get(cache_key) is not None,
                chunk is None,
            )
        ):
            return self[cache_key]

        self.debug(f"Requesting document from {link}")

        response = self._session.get(link)
        assert response.status_code == 200, "server responded with %d (%s)" % (
            response.status_code,
            response.text,
        )
        dump4mock("response.text@session.get(link)", True)
        dump4mock("response.content@session.get(link)", True)
        dump4mock("response.headers@session.get(link)", True)

        try:
            content_disposition = re.search(
                r'filename\="(.*)"', response.headers["Content-Disposition"]
            ).group(1)
        except BaseException:
            content_disposition = "unknown"

        dump4mock("content_disposition", True)
        content_length = int(response.headers["Content-Length"])
        dump4mock("content_length", True)

        self.debug("Successfully downloaded content")
        if chunk is None:
            result = (content_disposition, response.content, content_length)
            self[cache_key] = result
            return result
        return (
            content_disposition,
            response.iter_content(chunk_size=chunk),
            content_length,
        )
