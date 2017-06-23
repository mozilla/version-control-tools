# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import argparse
import logging
import os
import subprocess
import sys

import dulwich.repo
import hglib

from .git2hg import (
    linearize_git_repo_to_hg,
)
from .gitrewrite import (
    RewriteError,
    commit_metadata_rewriter,
)
from .gitrewrite.linearize import (
    linearize_git_repo,
)
from .overlay import (
    overlay_hg_repos,
    PushRaceError,
    PushRemoteFail,
)
from .servo_backout import (
    backout_servo_pr,
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
    (('--github-token',), dict(help='GitHub API token to use for GitHub API '
                                    'requests')),
]


def get_commit_rewriter_kwargs(args):
    """Obtain keyword arguments to pass to ``commit_metadata_rewriter()``"""
    kwargs = {}

    # Credentials are sensitive. Allow them to come from environment,
    # which isn't exposed in e.g. `ps`.
    for env in ('GITHUB_TOKEN',):
        v = os.environ.get(env)
        if v is not None:
            kwargs[env.lower()] = v

    for k in ('summary_prefix', 'reviewable_key',
              'remove_reviewable', 'source_repo_key',
              'source_revision_key', 'normalize_github_merge_message',
              'committer_action', 'use_p2_author',
              'github_token'):
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
    logging.getLogger('mozvcssync').setLevel(logging.INFO)


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

    kwargs = get_commit_rewriter_kwargs(args)

    if args.source_repo:
        kwargs['source_repo'] = args.source_repo

    repo = dulwich.repo.Repo(args.git_repo)
    rewriter = commit_metadata_rewriter(repo, **kwargs)

    try:
        linearize_git_repo(repo, args.ref,
                           exclude_dirs=args.exclude_dirs,
                           commit_rewriter=rewriter)
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
    parser.add_argument('--hg-push-url',
                        help='URL where to push converted Mercurial repo')
    # TODO this is a bit hacky. We should probably accept a full path.
    parser.add_argument('--shamap-s3-upload-url',
                        help='S3 path where SHA-1 map should be uploaded to')
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

    rewriter_args = get_commit_rewriter_kwargs(args)

    try:
        linearize_git_repo_to_hg(
            args.git_repo_url,
            args.git_ref,
            args.git_repo_path,
            args.hg_repo_path,
            git_push_url=args.git_push_url,
            hg_push_url=args.hg_push_url,
            move_to_subdir=args.move_to_subdir,
            find_copies_harder=args.find_copies_harder,
            skip_submodules=args.skip_submodules,
            similarity=args.similarity,
            shamap_s3_upload_url=args.shamap_s3_upload_url,
            git_commit_rewriter_args=rewriter_args,
            exclude_dirs=args.exclude_dirs)
    except RewriteError as e:
        logger.error('abort: %s' % str(e))
        sys.exit(1)
    except subprocess.CalledProcessError:
        sys.exit(1)


def overlay_hg_repos_cli():
    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--hg', help='hg executable to use')
    parser.add_argument('--into', required=True,
                        help='Subdirectory into which changesets will be '
                             'applied')
    parser.add_argument('source_repo_url',
                        help='URL of repository whose changesets will be '
                             'overlayed')
    parser.add_argument('dest_repo_url',
                        help='URL of repository where changesets will be '
                             'overlayed')
    parser.add_argument('dest_repo_path',
                        help='Local path to clone of <dest_repo_url>')
    parser.add_argument('--source_revs',
                        help='Revset describing changesets to overlay')
    parser.add_argument('--result-push-url',
                        help='URL where to push the overlayed result')
    parser.add_argument('--noncontiguous', action='store_true',
                        help='Allow a non-contiguous source_revs')

    args = parser.parse_args()

    if args.hg:
        hglib.HGPATH = args.hg

    configure_logging()

    MAX_ATTEMPTS = 3
    attempt = 0

    while attempt < MAX_ATTEMPTS:
        attempt += 1
        try:
            overlay_hg_repos(
                args.source_repo_url,
                args.dest_repo_url,
                args.dest_repo_path,
                source_rev=args.source_revs,
                dest_prefix=args.into,
                result_push_url=args.result_push_url,
                noncontiguous=args.noncontiguous)
            sys.exit(0)
        except PushRaceError:
            logger.warn('likely push race on attempt %d/%d' % (
                attempt, MAX_ATTEMPTS))
            if attempt < MAX_ATTEMPTS:
                logger.warn('retrying immediately...')
        except PushRemoteFail:
            logger.warn('push failed by remote on attempt %d/%d' % (
                attempt, MAX_ATTEMPTS))
            logger.warn('giving up since retry is likely futile')
            break
        except hglib.error.CommandError:
            logger.error('abort: hg command failed')
            sys.exit(1)
        except Exception as e:
            logger.exception('abort: %s' % str(e))
            sys.exit(1)

    logger.error('overlay not successful after %d attempts; try again '
                 'later' % attempt)
    sys.exit(1)


def servo_backout_pr_cli():
    # Unbuffer stdout.
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--hg',
                        help='hg executable to use')
    parser.add_argument('integration_repo_url',
                        help='URL to mercurial repository to scan for backout '
                             'commits')
    parser.add_argument('integration_repo_path',
                        help='Local path to clone of <integration_repo_url>')
    parser.add_argument('github_repo_name',
                        help='Github repository name to submit pull requests '
                             'to.  Must be in the form user/repo (eg. '
                             'servo/servo)')
    parser.add_argument('github_repo_path',
                        help='Local path to clone of <github_repo_name>')
    parser.add_argument('--author',
                        help='If provided sets the author of all pull '
                             'requests.  Defaults to the commit\'s author.')
    parser.add_argument('--tracking-s3-upload-url',
                        help='S3 path where the tracking file should be '
                             'uploaded to')
    parser.add_argument('--revision',
                        help='If provided start scanning commits at this '
                             'revision')
    args = parser.parse_args()
    if args.hg:
        hglib.HGPATH = args.hg

    configure_logging()

    try:
        backout_servo_pr(
            args.integration_repo_url,
            args.integration_repo_path,
            args.github_repo_name,
            args.github_repo_path,
            args.author,
            args.tracking_s3_upload_url,
            args.revision,
        )
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
