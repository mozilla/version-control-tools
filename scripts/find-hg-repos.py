#!/usr/bin/env python2.7
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Find Mercurial repositories under a specified path."""

import argparse
import errno
import grp
import os
import sys


def find_hg_repos(path):
    for root, dirs, files in os.walk(path):
        for d in sorted(dirs):
            if d == '.hg':
                yield root

        dirs[:] = [d for d in sorted(dirs) if d != '.hg']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', help='Group owner to search for')
    parser.add_argument('--requirement',
                        help='Repository requirement to search for')
    parser.add_argument('--no-requirement',
                        help='Missing repository requirement to search for')
    parser.add_argument('--upgrade-backup', action='store_true',
                        help='Find repositories that have a backup repo from '
                             'an upgrade')
    parser.add_argument('--obsstore', action='store_true',
                        help='Find repositories that have an obsolescence '
                             'store')
    parser.add_argument('paths', nargs='+')

    args = parser.parse_args()

    gid = None
    if args.group:
        try:
            group = grp.getgrnam(args.group)
            gid = group[2]
        except KeyError:
            print('group %s is not known' % args.group)
            sys.exit(1)

    def fltr(path):
        if gid is not None:
            st = os.stat(path)
            if st.st_gid != gid:
                return False

        if args.requirement or args.no_requirement:
            try:
                with open(os.path.join(path, '.hg', 'requires'), 'rb') as fh:
                    requirements = set(fh.read().split())
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise

                requirements = set()

            if args.requirement and args.requirement not in requirements:
                return False

            if args.no_requirement and args.no_requirement in requirements:
                return False

        if args.upgrade_backup:
            entries = os.listdir(os.path.join(path, '.hg'))
            if not any(e.startswith('upgradebackup.') for e in entries):
                return False

        if args.obsstore:
            p = os.path.join(path, '.hg', 'store', 'obsstore')
            if not os.path.exists(p):
                return False

        return True

    for d in args.paths:
        for path in find_hg_repos(d):
            if not fltr(path):
                continue

            print(path[len(d):])
