# -*- coding: utf-8 -*-

import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, TextIO, Union

import dill as pickle
from expiringdict import ExpiringDict

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

from .logger import Logger

####################
#                  #
# CACHE definition #
#                  #
####################


class Cache(ExpiringDict, Logger):
    """
    Abstraction Layer meant to be used as internal time-bound caching system.
    Class inherits from Logger and ExpiringDict (https://pypi.org/project/expiringdict).
    A SQLite 3 database will be utilized as secondary storage system.
    """

    # class attribute defining database name and location
    destination = ":memory:"

    @staticmethod
    def get_sqlite3_thread_safety(destination: str) -> int:
        """
        Static method used to retrieve correct thread safety level.
        (Further reading: https://www.sqlite.org/threadsafe.html)

        Positional arguments:
            destination: str,
                database name

        Returns
            int: platform dependend thread safety level
        """
        sqlite_threadsafe2python_dbapi = {0: 0, 2: 1, 1: 3}
        try:
            conn = sqlite3.connect(destination)
        except BaseException:
            # fallback to memory database
            conn = sqlite3.connect(":memory:")
        finally:
            threadsafety = conn.execute(
                """
                SELECT * FROM PRAGMA_COMPILE_OPTIONS
                WHERE COMPILE_OPTIONS LIKE 'THREADSAFE=%'
            """
            ).fetchone()[0]
            conn.close()
            return sqlite_threadsafe2python_dbapi[int(threadsafety.split("=")[1])]

    def __init__(
        self,
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
        Create a cache instance.
        Method initilizes Logger and Expiring Dict.

        Positional arguments:
            *args:
                Positional argument of Logger class.

        Keyword arguments
            max_age: int,
                TTL for records to cache in seconds.

            max_len: int,
                maximum number of records to be held in the cache.

            items: dict, optional,
                items to be copied from.

            destination: str,
                location of the internal database.

            **kwargs:
                Keyword arguments of Logger class.

        """
        ExpiringDict.__init__(
            self, max_len=max_len, max_age_seconds=max_age, items=items
        )
        Logger.__init__(
            self,
            *streams,
            filepath=filepath,
            filename=filename,
            emit=emit,
            verbose=verbose,
        )
        if destination:
            self.destination = destination
        if Cache.get_sqlite3_thread_safety(self.destination) == 3:
            check_same_thread = False
        else:
            check_same_thread = True
        try:
            self.conn = sqlite3.connect(
                self.destination,
                # allow multithread application access
                check_same_thread=check_same_thread,
                # disable database isolation to enable parallel access
                isolation_level=None,
            )
        except BaseException:
            self.destination = ":memory:"
            self.conn = sqlite3.connect(
                self.destination,
                check_same_thread=check_same_thread,
                isolation_level=None,
            )
        finally:
            self.debug("Caching into: %s" % self.destination)
            cursor = self.conn.cursor()
            # create table object for cached entries
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Cached(
                    Key TEXT PRIMARY KEY, 
                    Value BLOB NOT NULL,
                    InsertedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                );
            """
            )
            # create trigger to implement automatic expiration of cached records
            # trigger implements both constraints: max_age and max_len
            # trigged by an upsert operation
            cursor.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS Cleaner
                BEFORE INSERT ON Cached
                BEGIN
                    DELETE FROM Cached
                    WHERE Key in (
                        SELECT Key FROM Cached 
                        WHERE InsertedAt < datetime(CURRENT_TIMESTAMP, '-{max_age} seconds')
                    );
                    DELETE FROM Cached
                    WHERE Key in (
                        SELECT Key FROM Cached 
                        LIMIT -1 OFFSET {max_len}
                    );
                END;
            """
            )
            # load entries available in cache
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                SELECT Key, Value FROM Cached
                WHERE InsertedAt >= datetime(CURRENT_TIMESTAMP, '-{max_age} seconds');
            """
            )
            results = cursor.fetchall()
            for result in results:
                key, value = result
                # will trigger the SQL trigger automatically
                self[key] = pickle.loads(bytes.fromhex(value))

    def __getitem__(self, __k: str, __d: Any = None) -> Any:
        """
        Reimplementaion of dict.__getitem__.
        """

        # Find record in the SQLite databse
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            SELECT Value FROM Cached
            WHERE Key='{__k}' AND 
            InsertedAt >= datetime(CURRENT_TIMESTAMP, '-{self.max_age} seconds');
        """
        )
        result = cursor.fetchone()

        if result is None:
            raise KeyError(__k)

        # Compare retrieved reference with the internal one
        __s = pickle.loads(bytes.fromhex(result[0]))
        __i = super().__getitem__(__k, __d)
        # reference mismatch
        if id(__s) != id(__i):
            # mitigate reference mismatch (divergent memory address allocations)
            __s = __i
        self.debug("Retrieved from cache: %s@%d(%s)" % (__k, id(__s), type(__s)))
        return __s

    def __setitem__(self, __k: str, __v: Any, set_time: float = None):
        """
        Implementation of dict.__setitem__.
        """

        # Update inner state
        ExpiringDict.__setitem__(self, __k, __v, set_time)
        # Dump into database
        cursor = self.conn.cursor()
        # SQL statement wil trigger SQL trigger
        cursor.execute(
            """
            INSERT INTO Cached(Key, Value, InsertedAt)
            VALUES('{key}', '{value}', '{now}')
            ON CONFLICT DO
            UPDATE SET Value='{value}';
            """.format(
                key=__k,
                value=pickle.dumps(__v, protocol=pickle.HIGHEST_PROTOCOL).hex(),
                now=(
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    if set_time is None
                    else datetime.fromtimestamp(set_time).strftime("%Y-%m-%d %H:%M:%S")
                ),
            )
        )
        self.debug("Cached: %s@%d(%s)" % (__k, id(__v), type(__v)))

    def __delitem__(self, __k: str):
        """
        Implementation of dict.__delitem__.
        """

        # Update inner state
        ExpiringDict.__delitem__(self, __k)
        cursor = self.conn.cursor()
        # SQL statement wil trigger SQL trigger
        cursor.execute(
            """
            DELETE FROM Cached
            WHERE Key = '{key}';
            """.format(
                key=__k
            )
        )
        self.debug("Removed: %s" % __k)

    def prolongate(self, key: str, seconds: Union[float, int]):
        """
        Moves the creation timestamp of chached record int .

        Positional arguments:
            key: str,
                item id.

            seconds: Union[float, int],
                offset from now by which creation date will be moved into the future.
        """

        __v = self.__getitem__(key)
        self.__delitem__(key)
        return self.__setitem__(key, __v, set_time=(time.time() + seconds))

    def __del__(self):
        """
        Tear-down for garbage collector.
        """

        if hasattr(self, "conn"):
            self.conn.close()
