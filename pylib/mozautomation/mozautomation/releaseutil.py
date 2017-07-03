# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Code for gluing the release scraper and database together."""

from __future__ import absolute_import, print_function, unicode_literals

import datetime

from . import (
    releasedb,
    releasescraper,
)


def import_nightly_builds(database_path, repo, start_day=None):
    db = releasedb.FirefoxReleaseDatabase(database_path)
    state = db.get_all_state()

    if not start_day:
        if 'last_nightly_day' in state:
            year, month, day = map(int, state['last_nightly_day'].split('-'))
            last_day = datetime.date(year, month, day)
            start_day = last_day - datetime.timedelta(days=2)
            print('using %s as start day calculated from last seen day %s' % (
                start_day, last_day))
        else:
            # This is the earliest day we can import Nightly releases for.
            start_day = datetime.date(2010, 4, 1)
            print('using %s as Nightly start day because no state seen' %
                  start_day)

    nightly_builds = releasescraper.find_nightly_builds(start_day)
    nightly_builds = releasescraper.ensure_full_revision(nightly_builds,
                                                         repo)

    return db.import_nightly_builds(nightly_builds)
