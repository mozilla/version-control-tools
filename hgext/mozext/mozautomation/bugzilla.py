# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import unicode_literals

from mozautomation.firefoxprofile import (
    find_profiles,
    get_cookies,
)

def get_cookie_auth(host='bugzilla.mozilla.org'):
    """Obtain Bugzilla auth cookies from Firefox.

    This returns an iterable of 2-tuples of (login, cookie) sorted by the
    preferred usage order.
    """

    profiles = find_profiles(find_times=True)

    auths = []
    for name, path, is_default, newest_time in profiles:
        login, auth = None, None
        for cookie in get_cookies(path, host=host):
            if cookie['name'] == 'Bugzilla_login':
                login = cookie['value']
            elif cookie['name'] == 'Bugzilla_logincookie':
                auth = cookie['value']

        if login and auth:
            auths.append((login, auth, is_default, newest_time))

    def cmp(a, b):
        if a[2]:
            return -1
        elif b[2]:
            return 1

        if a[3] > b[3]:
            return -1
        elif a[3] < b[3]:
            return 1
        else:
            return 0

    auths = sorted(auths, cmp=cmp)

    return [(e[0], e[1]) for e in auths]
