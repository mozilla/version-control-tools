#!/usr/bin/env python3.6
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Upgrade Mercurial repositories.

Given a list of repository paths on stdin, run `hg debugupgraderepo` on those
repositories.

The list of repository paths is assumed to absolute or relative to the
current directory.
"""

import argparse
import collections
import datetime
import concurrent.futures
import os
import pathlib
import stat
import subprocess
import sys

RECOGNIZED_GROUPS = {
    'hg',
    'hg_embedding',
    'scm_autoland',
    'scm_conduit',
    'scm_level_1',
    'scm_level_2',
    'scm_level_3',
    'scm_l10n',
    'scm_l10n_infra',
    'scm_l10n_drivers',
    'scm_nss',
}

HERE = pathlib.Path(os.path.normpath(os.path.abspath(os.path.dirname(
    __file__))))
REPO_PERMISSIONS = HERE / 'repo-permissions'
assert REPO_PERMISSIONS.exists()


def guess_group_owner(path):
    groups = collections.Counter()
    try:
        group = path.group()
    except KeyError:
        group = path.stat().st_gid

    groups[group] += 1

    for p in path.iterdir():
        try:
            group = p.group()
        except KeyError:
            group = p.stat().st_gid

        groups[group] += 1

    return groups.most_common(1)[0][0]


def validate_repo(path):
    hg_dir = path / '.hg'

    if not os.path.isdir(path):
        print('%s is not a directory' % path)
        return False

    # We require that repos have consistent ownership so we know that changing
    # ownership post upgrade doesn't cause chaos.
    file_modes = set()
    directory_modes = set()

    for p in hg_dir.iterdir():
        st = p.stat()

        if stat.S_ISDIR(st.st_mode):
            directory_modes.add(stat.filemode(st.st_mode))
        else:
            file_modes.add(stat.filemode(st.st_mode))

    valid = True

    group = guess_group_owner(hg_dir)
    if group not in RECOGNIZED_GROUPS:
        print('%s has unrecognized group: %s' % (path, group))
        valid = False

    if len(directory_modes) > 1:
        print('%s has multiple directory file modes' % path)
        valid = False

    if len(file_modes) > 1:
        print('%s has multiple file modes' % path)
        valid = False

    return valid


def run_and_log(args, cwd, log_handle, prefix):
    log_handle.write('%s $ %s\n' % (
        datetime.datetime.utcnow().isoformat(), ' '.join(args)))
    print('%s> $ %s' % (prefix, ' '.join(args)), flush=True)

    env = dict(os.environ)
    env['COLUMNS'] = '80'

    p = subprocess.Popen(args, cwd=cwd, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         bufsize=1, universal_newlines=True, encoding='latin1')

    terminated = False
    with p:
        while True:
            try:
                line = p.stdout.readline()
                if not line:
                    break

                now = datetime.datetime.utcnow()
                log_handle.write('%s %s' % (now.isoformat(), line))
                print('%s> %s' % (prefix, line), end='', flush=True)
            except KeyboardInterrupt:
                p.terminate()
                terminated = True

    log_handle.write('%s [%d]\n' % (
        datetime.datetime.utcnow().isoformat(), p.returncode))
    print('%s> [%d]' % (prefix, p.returncode), flush=True)

    if terminated:
        raise KeyboardInterrupt('re-raising KeyboardInterrupt')

    return p.returncode


def upgrade_repo(path, dry_run=False):
    hg_dir = path / '.hg'

    group = guess_group_owner(hg_dir)

    args = [
        '/usr/bin/python', '-u',
        '/usr/bin/hg',
        # This makes it easier to tell which repo the process is operating on.
        '--cwd', str(path.resolve()),
        '--pager=never',
        # Some of our extensions either don't work with the system `hg` or we
        # don't want them to run.
        '--config', 'extensions.mozhooks=!',
        '--config', 'extensions.vcsreplicator=!',
        '--config', 'hooks.pretxnclose.populate_caches=true',
        '--config', 'progress.delay=1.0',
        '--config', 'progress.refresh=10.0',
        '--config', 'progress.assume-tty=true',
        'debugupgraderepo',
        # This will force re-delta if the existing delta parent isn't the
        # DAG parent. And it will compute deltas against both parents and
        # pick the smallest one.
        '--optimize', 'redeltamultibase',
    ]

    if not dry_run:
        args.append('--run')

    log_path = hg_dir / 'upgrade.log'
    with log_path.open('a', buffering=1) as log:
        log_path.chmod(0o664)
        p = run_and_log(args, path, log, path)
        if p:
            return False

        # Adjust repository permissions.
        args = [
            str(REPO_PERMISSIONS),
            '.',
            'hg',
            group,
            'wwr',
        ]
        p = run_and_log(args, path, log, path)
        if p:
            return False

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help='Do not perform upgrade')
    parser.add_argument('-j', type=int, default=1,
                        help='Number of workers')

    args = parser.parse_args()

    valid = True

    repos = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        repo = pathlib.Path(line)
        if not validate_repo(repo):
            valid = False

        repos.append(repo)

    if not valid:
        sys.exit(1)

    res = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.j) as e:
        fs = []
        for repo in repos:
            fs.append(e.submit(upgrade_repo, repo, dry_run=args.dry_run))

        for f in concurrent.futures.as_completed(fs):
            try:
                if not f.result():
                    res = 1
            except Exception as e:
                res = 1
                print(e)

    sys.exit(res)
