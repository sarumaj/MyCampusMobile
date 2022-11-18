# -*- coding: utf-8 -*-

import logging
import os
import sys

# trunk-ignore(flake8/F401)
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, TextIO


class Logger(logging.LoggerAdapter):
    def __init__(
        self,
        *streams: tuple[TextIO],
        filepath: str,
        filename: Optional[str] = "app.log",
        emit: Optional[bool] = True,
        verbose: Optional[bool] = False,
        user: Optional[str] = None,
    ) -> type[logging.LoggerAdapter]:
        """
        Create a logging Logger instance
        based on the basic configuration
        of the 'logging' module and 'filepath' argument,
        installs stream handlers and configures
        extra format arguments for log records.

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

        Returns:
            type[logging.LoggerAdapter]
        """

        # get logger instance
        logger = logging.getLogger(Path(filepath).name)
        # set log level
        logger.setLevel((logging.DEBUG if verbose else logging.INFO))
        # set log format
        formatter = logging.Formatter(
            fmt=" - ".join(
                (
                    # logger name and process id
                    "where: %(name)s (%(process)06d)",
                    # timestamp
                    "when: %(asctime)s",
                    # custom attribute
                    "who: %(user)s",
                    # log level and log message
                    "%(levelname)s: %(message)s",
                )
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # remove all handlers if any
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
        # collect new handlers
        handlers = []
        if isinstance(filename, str):
            # add log file handler
            handlers.append(
                # rotating log file handler will close the log file
                # rename it and open a new one as soon as the log
                # file size exceeds predefined size limit
                logging.handlers.RotatingFileHandler(
                    filename=(
                        # check if filepath is directory or file
                        Path(filepath) / filename
                        if Path(filepath).is_dir()
                        else Path(filepath).parent / filename
                    ),
                    mode="a",  # append contents
                    maxBytes=5 * 1_024**2,  # allow max size of 5 MBytes
                    backupCount=1,  # keep only one backup log on rotation
                    encoding="utf-8",  # charset
                )
            )

        for stream in streams:
            # add additional stream handlers if required
            if stream not in (sys.stdout, sys.stderr):
                handlers.append(logging.StreamHandler(stream))
        if emit or not isinstance(filename, str):
            # set stream handlers for console
            for level, handler in zip(
                ((logging.DEBUG if verbose else logging.INFO), logging.ERROR),
                (logging.StreamHandler(sys.stdout), logging.StreamHandler(sys.stderr)),
            ):
                handler.setLevel(level)
                handlers.append(handler)
        for handler in handlers:
            # add handlers to the logger instance
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        # adapt logger to include custom content in the log messages
        super().__init__(logger, extra={"user": user if user else os.getlogin()})
