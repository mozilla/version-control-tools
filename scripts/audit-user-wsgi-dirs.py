#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Look for problems in WSGI directories for user repositories."""

import os
import sys

def find_hg_repos(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            if d == '.hg':
                yield root

        dirs[:] = [d for d in dirs if d != '.hg']

def active_users(root):
    users = set()
    root = os.path.join(root, 'mozilla', 'users')
    for repo in find_hg_repos(root):
        user = os.path.basename(os.path.dirname(repo))
        users.add(user)

    return users

def wsgi_user_dirs(root):
    users = {}

    root = os.path.join(root, 'webroot_wsgi', 'users')
    for d in os.listdir(root):
        full = os.path.join(root, d)
        if d.startswith('.'):
            continue

        if not os.path.isdir(full):
            continue

        config_path = os.path.join(full, 'hgweb.config')
        wsgi_path = os.path.join(full, 'hgweb.wsgi')

        users[d] = (os.path.exists(config_path), os.path.exists(wsgi_path))

    return users

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('usage: %s root' % sys.argv[0])
        sys.exit(1)

    root = sys.argv[1]
    wanted = active_users(root)
    present = wsgi_user_dirs(root)
    present_users = set(present.keys())

    for user in sorted(present_users - wanted):
        print('old user wsgi dir: %s' % user)
    for user in sorted(wanted - present_users):
        print('missing user wsgi dir: %s' % user)

    for user, (have_config, have_wsgi) in sorted(present.items()):
        if user not in wanted:
            continue

        if not have_config:
            print('missing hgweb.config: %s' % user)
        if not have_wsgi:
            print('missing hgweb.wsgi: %s' % user)
