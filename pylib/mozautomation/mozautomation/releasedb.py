# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Store Firefox release information in a SQLite database."""

from __future__ import absolute_import, unicode_literals

import contextlib
import datetime
import json
import os
import sqlite3


def _ts_to_day(ts):
    return datetime.datetime.utcfromtimestamp(ts).date()


def build_anchor(build):
    """Create an identifier unique to each release build"""
    return b"%s%s%s%s" % (
        build[b"revision"][0:12],
        build[b"channel"],
        build[b"platform"],
        build[b"build_id"],
    )


class FirefoxReleaseDatabase(object):
    """Persistently store Firefox release information in a database.

    Insertions to the database should *always* go through this module so
    behavior is understood. Reads can be performed by other consumers easily
    enough.

    The following tables exist:

    builds
       Each row describes a Firefox release. Pretty simple.
    state
       Key-value pairs tracking database / import state.

    An "insertion key" is associated with every build. This is an integer value
    basically tracking the age of each entry. Newer rows should have larger
    insertion key values. This key is used to facilitate replication of the
    database (mirrors can track their last seen insertion key and only request
    newer data). The big assertion is that there is only a single process
    importing and therefore no races to update the insertion key.
    """

    def __init__(self, path, bytestype=bytes):
        self.path = path

        self.created = False
        if not os.path.exists(path):
            self.created = True

        self._db = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

        # Preserve TEXT data as bytes.
        self._db.text_factory = bytestype

        # Sacrifice robustness for speed. If we lose the db, we can always
        # rebuild it by doing a full scan.
        self._db.execute("PRAGMA SYNCHRONOUS=OFF")
        self._db.execute("PRAGMA JOURNAL_MODE=WAL")

        self._create_schema(self._schema_version())

    def _schema_version(self):
        return self._db.execute("PRAGMA user_version").fetchone()[0]

    def _create_schema(self, existing):
        if existing > 1:
            raise Exception(
                "unknown schema version detected; did you downgrade code?"
            )

        with self._db:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS builds ("
                "insertion_key INTEGER, "
                "channel TEXT, "
                "platform TEXT, "
                "build_id TEXT, "
                "app_version TEXT, "
                "revision TEXT, "
                "day INTEGER, "
                "artifacts_url TEXT, "
                "UNIQUE (revision, channel, platform, build_id)"
                ")"
            )

            self._db.execute(
                "CREATE INDEX IF NOT EXISTS i_builds_revision ON builds (revision)"
            )

            self._db.execute(
                "CREATE INDEX IF NOT EXISTS i_builds_insertion_key "
                "ON builds (insertion_key)"
            )

            self._db.execute(
                "CREATE TABLE IF NOT EXISTS state ("
                "key TEXT PRIMARY KEY, "
                "value TEXT "
                ")"
            )

            self._db.execute(
                "INSERT OR IGNORE INTO state VALUES (?, ?)", ("insertion_key", "0")
            )

            self._db.execute("PRAGMA user_version=1")

    def _insert_build(self, build, insertion_key):
        if len(build[b"revision"]) != 40:
            raise ValueError("expected 40 character revision")

        day = build[b"day"]
        ts = datetime.datetime(day.year, day.month, day.day) - datetime.datetime(
            1970, 1, 1
        )
        ts = ts.total_seconds()

        self._db.execute(
            "INSERT OR REPLACE INTO builds VALUES (?, ?, ?, ?, ?, ?, ?, ?) ",
            (
                insertion_key,
                build[b"channel"],
                build[b"platform"],
                build[b"build_id"],
                build[b"app_version"],
                build[b"revision"],
                ts,
                build[b"artifacts_url"],
            ),
        )

    def import_nightly_builds(self, builds):
        """Import an iterable of Nightly builds into the database.

        Build instances are dicts as returned by
        ``releasescraper.find_nightly_builds()``.
        """
        count = 0
        with self._db:
            # Find current builds so we can perform duplicate detection.
            previous_builds = {build_anchor(build) for build in self.builds()}

            state = self.get_all_state()

            insertion_key = int(state[b"insertion_key"]) + 1

            if b"last_nightly_day" in state:
                y, m, d = map(int, state[b"last_nightly_day"].split(b"-"))
                last_day = datetime.date(y, m, d)
            else:
                last_day = datetime.date(1900, 1, 1)

            for build in builds:
                if build_anchor(build) in previous_builds:
                    continue

                self._insert_build(build, insertion_key)
                last_day = max(last_day, build[b"day"])
                count += 1

            if count:
                self._set_state(
                    b"last_nightly_day", last_day.strftime("%Y-%m-%d").encode("utf-8")
                )
                self._set_state(b"insertion_key", insertion_key)

        return count

    def get_all_state(self):
        """Obtain a dict of all state values."""
        s = {}

        for row in self._db.execute("SELECT key, value FROM state"):
            s[row[0]] = row[1]

        return s

    def _set_state(self, key, value):
        """Set state value for a key."""
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO state VALUES (?, ?)", (key, value))

    def builds(self):
        """Obtain an iterable of builds."""
        q = (
            "SELECT channel, platform, build_id, app_version, revision, "
            "day, artifacts_url "
            "FROM builds "
            "ORDER BY build_id DESC, platform ASC"
        )

        for row in self._db.execute(q):
            channel, platform, build_id, app_version, revision, ts, archive_url = row

            day = _ts_to_day(ts)

            build = {
                b"app_version": app_version,
                b"artifacts_url": archive_url,
                b"build_id": build_id,
                b"channel": channel,
                b"day": day,
                b"platform": platform,
                b"revision": revision,
            }

            yield build

    def serialize_builds(self, start_insertion_key=None):
        """Emit a serialized represention of builds.

        Emitted strings don't have newlines, so that is one method for
        delimiting records in a stream.
        """
        q = (
            "SELECT insertion_key, channel, platform, build_id, app_version, "
            "revision, day, artifacts_url "
            "FROM builds "
        )

        if start_insertion_key:
            q += "WHERE insertion_key >= ? "
            params = (start_insertion_key,)
        else:
            params = ()

        q += "ORDER BY insertion_key ASC, build_id ASC, platform ASC"

        for row in self._db.execute(q, params):
            (
                insertion_key,
                channel,
                platform,
                build_id,
                app_version,
                revision,
                day,
                archives_url,
            ) = row

            yield json.dumps(
                {
                    b"_format": 1,
                    b"insertion_key": insertion_key,
                    b"channel": channel,
                    b"platform": platform,
                    b"build_id": build_id,
                    b"app_version": app_version,
                    b"revision": revision,
                    b"day": day,
                    b"archives_url": archives_url,
                },
                sort_keys=True,
            )

    def import_serialized(self, data):
        """Import data records produced via ``serialize_builds()``.

        The assertion is that builds are exported and imported by insertion_key.
        Therefore, old data belonging to an incoming insertion key will be
        dropped and replaced by the incoming data.
        """
        params = (
            "insertion_key",
            "channel",
            "platform",
            "build_id",
            "app_version",
            "revision",
            "day",
            "artifacts_url",
        )

        insertion_keys = set()

        builds = []
        for entry in data:
            build = json.loads(entry)

            if build["_format"] != 1:
                raise Exception("unknown data format %s" % build["_format"])

            insertion_keys.add(build["insertion_key"])
            builds.append(tuple(build[k] for k in params))

        with self._db:
            for k in insertion_keys:
                self._db.execute("DELETE FROM builds WHERE insertion_key=?", (k,))

            self._db.executemany(
                "INSERT OR REPLACE INTO builds VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                builds,
            )

            return len(builds)

    def unique_release_configurations(self, fltr=None):
        """Obtain a set of unique release configurations.

        ``fltr`` can be specified to limit which database entries are
        examined.
        """
        configs = set()

        for build in self.builds():
            if fltr and not fltr(build):
                continue

            configs.add((build[b"channel"], build[b"platform"]))

        return configs

    @contextlib.contextmanager
    def cache_builds(self):
        """Caches data when the context manager is active."""
        monkey_patched = False

        if b"builds" not in self.__dict__:
            builds = list(self.builds())

            # Monkeypatch self.builds() with a function that returns a cached copy.
            def cachedbuilds():
                return iter(builds)

            self.builds = cachedbuilds

        try:
            yield
        finally:
            if monkey_patched:
                del self.__dict__[b"builds"]
