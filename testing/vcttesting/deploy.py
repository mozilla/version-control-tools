# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import json
import logging
import os
from pipes import quote
import subprocess

from .util import get_and_write_vct_node

HERE = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ANSIBLE = os.path.join(ROOT, 'ansible')

logger = logging.getLogger(__name__)


def run_playbook(name, extra_vars=None, verbosity=0):
    get_and_write_vct_node()

    extra_vars = extra_vars or {}

    args = [
        'ansible-playbook',
        '-i', os.path.join(ANSIBLE, 'hosts'),
        '-f', '20',
        '%s.yml' % name,
        '--extra-vars', json.dumps(extra_vars),
    ]
    if verbosity:
        args.append('-%s' % ('v' * verbosity))

    logger.info('$ %s' % ' '.join([quote(a) for a in args]))
    return subprocess.call(args, cwd=ANSIBLE)


def deploy_mozreview_dev(repo=None, rev=None, verbosity=0):
    extra = {'vct': ROOT}
    if repo:
        extra['repo'] = repo
    if rev:
        extra['rev'] = rev

    return run_playbook('deploy-mozreview-dev', extra_vars=extra,
                        verbosity=verbosity)


def deploy_mozreview_prod(repo=None, rev=None, verbosity=0):
    extra = {'vct': ROOT}
    if repo:
        extra['repo'] = repo
    if rev:
        extra['rev'] = rev

    return run_playbook('deploy-mozreview-prod', extra_vars=extra,
                        verbosity=verbosity)


def mozreview_create_repo(verbosity=0):
    extra = {'vct': ROOT}
    return run_playbook('mozreview-create-repo', extra_vars=extra,
                        verbosity=verbosity)


def deploy_hgmo(verbosity=0):
    """Deploy to hg.mozilla.org."""
    extra = {'vct': ROOT}

    return run_playbook('deploy-hgmo', extra_vars=extra,
                        verbosity=verbosity)


def hgmo_strip(repo, rev, verbosity=0):
    extra = {
        'repo': repo,
        'rev': rev,
    }

    return run_playbook('hgmo-strip-repo', extra_vars=extra,
                        verbosity=verbosity)


def hgmo_reclone_repos(repos, verbosity=0):
    extra = {'repos': repos}

    return run_playbook('hgmo-reclone-repos', extra_vars=extra,
                        verbosity=verbosity)
