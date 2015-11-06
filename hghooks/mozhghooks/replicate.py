# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Hook to perform and record replication."""

import os
import pwd
import subprocess
import time

from mercurial import (
    extensions,
)


def changegrouphook(ui, repo, **kwargs):
    return _replicate(ui, repo, 'changegroup')


def pushkeyhook(ui, repo, namespace, **kwargs):
    return _replicate(ui, repo, namespace)


def _replicate(ui, repo, what):
    if not repo.root.startswith('/repo/hg/mozilla'):
        ui.write('repository not eligible for replication\n')
        return 0

    # Do not perform replication when the experimental vcsreplicator extension
    # is loaded. (The extension should be loaded by per-repo .hg/hgrc files for
    # until it is generally deployed.)
    try:
        extensions.find('vcsreplicator')
        ui.write('legacy replication of %s disabled because vcsreplicator '
                 'is loaded\n' % what)
        return 0
    except Exception:
        pass

    relpath = repo.root[len('/repo/hg/mozilla/'):]
    args = ['/usr/local/bin/repo-push.sh', relpath]

    user = pwd.getpwuid(os.getuid()).pw_name
    if user != 'hg':
        args = ['/usr/bin/sudo', '-u', 'hg'] + args

    t0 = time.time()

    with open(os.devnull, 'w') as null:
        res = subprocess.call(args, stdout=null, stderr=subprocess.STDOUT,
                              cwd='/')

    t1 = time.time()
    status = 'completed successfully' if res == 0 else 'errored'
    msg = 'replication of %s data %s in %.1fs\n' % (what, status, t1 - t0)
    ui.write(msg)
    ui.log('replication', msg)

    # We don't currently let replication success dictate the result of the
    # hook. This is a post transaction hook anyway, so failure likely doesn't
    # do anything.
    return 0
