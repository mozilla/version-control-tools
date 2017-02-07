# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import argparse
import logging
import os
import subprocess
import sys

import hglib

from .git2hg import (
    linearize_git_repo_to_hg,
)
from .gitrewrite import (
    RewriteError,
)
from .gitrewrite.linearize import (
    linearize_git_repo,
)


logger = logging.getLogger(__name__)


LINEARIZE_GIT_ARGS = [
    (('--exclude-dir',), dict(action='append', dest='exclude_dirs',
                              help='Directory to exclude from rewritten '
                                   'history')),
    (('--summary-prefix',), dict(help='String to prefix commit message '
                                      'summary line with')),
    (('--reviewable-key',), dict(help='Commit message key to replace '
                                      'Reviewable Markdown blocks with')),
    (('--remove-reviewable',), dict(action='store_true',
                                    help='Remove Reviewable.io Markdown blocks')),
    (('--source-repo-key',), dict(help='Commit message key that source '
                                       'repository should be recorded under')),
    (('--source-revision-key',), dict(help='Commit message key that original '
                                           'source revision should be stored '
                                           'under')),
    (('--normalize-github-merge-message',), dict(
        action='store_true',
        help='Rewrite commit messages for GitHub pull request merges '
             'to be more sensible for linearized repos')),
    (('--committer-action',), dict(choices={'keep', 'use-author',
                                             'use-committer'},
                                    help='What to do with committer field in'
                                         'Git commits')),
    (('--author-map',), dict(help='File containing mapping of old to new '
                                  'commit author/committer values')),
    (('--use-p2-author',), dict(action='store_true',
                                help='Use the author of the 2nd parent for '
                                     'merge commits')),
    (('--github-username',), dict(help='Username to use for GitHub API '
                                       'requests')),
    (('--github-token',), dict(help='GitHub API token to use for GitHub API '
                                    'requests')),
]


def get_git_linearize_kwargs(args):
    kwargs = {}

    # Credentials are sensitive. Allow them to come from environment,
    # which isn't exposed in e.g. `ps`.
    for env in ('GITHUB_USERNAME', 'GITHUB_TOKEN'):
        v = os.environ.get(env)
        if v is not None:
            kwargs[env.lower()] = v

    for k in ('exclude_dirs', 'summary_prefix', 'reviewable_key',
              'remove_reviewable', 'source_repo_key',
              'source_revision_key', 'normalize_github_merge_message',
              'committer_action', 'use_p2_author',
              'github_username', 'github_token'):
        v = getattr(args, k)
        if v is not None:
            kwargs[k] = v

    if args.author_map:
        author_map = {}
        with open(args.author_map, 'rb') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith(b'#'):
                    continue

                old, new = line.split(b'=')
                author_map[old.strip()] = new.strip()

        kwargs['author_map'] = author_map

    return kwargs


def configure_logging():
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    root.addHandler(handler)


def linearize_git():
    parser = argparse.ArgumentParser()
    for args, kwargs in LINEARIZE_GIT_ARGS:
        parser.add_argument(*args, **kwargs)

    parser.add_argument('--source-repo',
                        help='URL of repository being converted')
    parser.add_argument('git_repo', help='Path to Git repository to linearize')
    parser.add_argument('ref', help='ref to linearize')

    args = parser.parse_args()

    configure_logging()

    kwargs = get_git_linearize_kwargs(args)

    if args.source_repo:
        kwargs['source_repo'] = args.source_repo

    try:
        linearize_git_repo(args.git_repo, args.ref, **kwargs)
    except RewriteError as e:
        logger.error('abort: %s' % str(e))


def linearize_git_to_hg():
    parser = argparse.ArgumentParser()
    for args, kwargs in LINEARIZE_GIT_ARGS:
        parser.add_argument(*args, **kwargs)

    parser.add_argument('--hg', help='hg executable to use')
    parser.add_argument('--move-to-subdir',
                        help='Move the files in the Git repository under a '
                             'different subdirection in the destination repo')
    parser.add_argument('--copy-similarity', type=int, default=50,
                        dest='similarity',
                        help='File % similarity for it to be identified as a '
                             'copy')
    parser.add_argument('--find-copies-harder', action='store_true',
                        help='Work harder to find file copies')
    parser.add_argument('--skip-submodules', action='store_true',
                        help='Skip processing of Git submodules')
    parser.add_argument('--git-push-url',
                        help='URL where to push converted Git repo')
    parser.add_argument('git_repo_url',
                        help='URL of Git repository to convert')
    parser.add_argument('git_ref', help='Git ref to convert')
    parser.add_argument('git_repo_path', help='Local path of where to store '
                                              'Git repo clone')
    parser.add_argument('hg_repo_path', help='Local path of where to store '
                                             'Mercurial conversion of repo')


    args = parser.parse_args()

    if args.hg:
        hglib.HGPATH = args.hg

    configure_logging()

    kwargs = get_git_linearize_kwargs(args)
    for k in ('similarity', 'find_copies_harder', 'skip_submodules',
              'move_to_subdir', 'git_push_url'):
        v = getattr(args, k)
        if v is not None:
            kwargs[k] = v

    try:
        linearize_git_repo_to_hg(
            args.git_repo_url,
            args.git_ref,
            args.git_repo_path,
            args.hg_repo_path,
            **kwargs)
    except RewriteError as e:
        logger.error('abort: %s' % str(e))
        sys.exit(1)
    except subprocess.CalledProcessError:
        sys.exit(1)
