# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import logging
import os
import subprocess

import hglib

from .util import (
    run_hg,
)


logger = logging.getLogger(__name__)


class PushRaceError(Exception):
    """Raised when a push fails due to new heads on a remote."""


class PushRemoteFail(Exception):
    """Raised when a push fails due to an error on the remote."""


def overlay_hg_repos(source_repo_url, dest_repo_url, dest_repo_path,
                     dest_prefix, source_rev=None, dest_rev='tip',
                     result_push_url=None, noncontiguous=False, notify=None):
    """Overlay changesets from an hg repo into a sub-directory of another.

    This function will take changesets from the Mercurial repo
    at ``source_url`` and apply them to the Mercurial repo at
    ``dest_repo_url``, rewriting file paths so they are stored in
    the directory ``dest_prefix`` of the destination repository.

    A copy of ``dest_repo_url`` is managed at ``dest_repo_path``,
    which is where all the activity occurs.

    If ``source_rev`` is specified, it is evaluated as a revset
    against ``source_repo_url`` and only the returned changesets
    will be converted. If not defined, the default used by
    ``hg overlay`` is used.

    ``dest_rev`` is the revision in ``dest_repo_url`` on top of which
    changesets should be overlayed. By default, the ``tip`` of the
    repository is used. This will have undefined behavior if the repo
    has multiple heads. You have been warned.
    """
    if not os.path.exists(dest_repo_path):
        logger.warn('%s does not exist; cloning %s' % (
                    dest_repo_path, dest_repo_url))
        subprocess.check_call([hglib.HGPATH, b'clone', b'--noupdate',
                               b'--pull', dest_repo_url, dest_repo_path])

    configs = (
        b'extensions.strip=',
    )

    with hglib.open(dest_repo_path, 'utf-8', configs) as hrepo:
        # Purge local repo of unwanted changesets.
        try:
            run_hg(logger, hrepo,
                   [b'strip', b'--no-backup', b'-r', b'not public()'])
        except hglib.error.CommandError as e:
            if b'empty revision set' not in e.out:
                raise
            logger.warn('(ignoring strip failure)')

        # Resolve the destination revision.
        logger.warn('resolving destination revision: %s' % dest_rev)
        out = run_hg(logger, hrepo,
                     [b'identify', dest_repo_url, b'-r', dest_rev])

        out = out.split()[0]
        if len(out) != 12:
            raise Exception('%s did not resolve to 12 character node' %
                            dest_rev)

        dest_rev = out

        if dest_rev not in hrepo:
            logger.warn('pulling %s to obtain %s' % (dest_repo_url, dest_rev))
            run_hg(logger, hrepo, [b'pull', b'-r', dest_rev, dest_repo_url])

        dest_node = hrepo[dest_rev].node()
        old_tip = hrepo[b'tip']

        # The destination revision is now present locally. Commence the overlay!
        args = [
            b'overlay',
            source_repo_url,
            b'--into', dest_prefix,
            b'-d', dest_node,
        ]

        if noncontiguous:
            args.append('--noncontiguous')
        if notify:
            args.extend(['--notify', notify])

        if source_rev:
            args.append(source_rev)

        logger.warn('commencing overlay of %s' % source_repo_url)
        run_hg(logger, hrepo, args)

        new_tip = hrepo[b'tip']
        if new_tip.rev() == old_tip.rev():
            logger.warn('no changesets overlayed')
            return

        new_count = new_tip.rev() - old_tip.rev()
        logger.warn('%d new changesets; new tip is %s' % (
                    new_count, new_tip.node()))

        # As a sanity check, verify the new changesets are only in a single
        # head.
        new_heads = hrepo.log(revrange=b'heads(%d:)' % (old_tip.rev() + 1))
        if len(new_heads) != 1:
            raise Exception('multiple new heads after overlay; you likely '
                            'found a bug!')

        if not result_push_url:
            return

        logger.warn('pushing %d new changesets on head %s to %s' % (
                    new_count, new_tip.node(), result_push_url))
        for rev in hrepo.log(revrange=b'%d::%s' % (old_tip.rev() + 1,
                                                   new_tip.node())):
            logger.warn('%s:%s: %s' % (rev[0], rev[1][0:12],
                                       rev[5].decode('utf-8').splitlines()[0]))

        try:
            run_hg(logger, hrepo,
                   [b'push', b'-r', new_tip.node(), result_push_url])
        except hglib.error.CommandError as e:
            # Detect likely push race and convert exception so caller
            # can retry.
            if b'push creates new remote head' in e.out:
                raise PushRaceError(e.out)
            elif b'push failed on remote' in e.out:
                raise PushRemoteFail(e.out)
            raise
