# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Functionality for "linearizing" a Git repository.

This takes a repository with merge commits and rewrites commits to remove
the merges, yielding a clean, linear history.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import re
import subprocess

import dulwich.repo
import github3

from . import (
    prune_directories,
    rewrite_commit_message,
    RewriteError,
)


logger = logging.getLogger(__name__)


def linearize_git_repo(git_repo, ref, exclude_dirs=None,
                       summary_prefix=None,
                       reviewable_key=None,
                       remove_reviewable=False,
                       normalize_github_merge_message=False,
                       source_repo_key=None, source_repo=None,
                       source_revision_key=None,
                       committer_action='keep',
                       author_map=None,
                       use_p2_author=False,
                       github_username=None, github_token=None):
    """Linearize a ref in a Git repository.

    The commits in the ref will be rewritten to only include first parent
    ancestry. i.e. all merge commits will be removed. All commits from the
    non-first-parent ancestry will be dropped.

    As a side-effect of conversion, the refs ``refs/convert/source/<ref>`` and
    ``refs/convert/dest/<ref>`` will be written containing pointers to the
    last converted commit (identical to ``ref``) and its new, converted
    commit, respectively. Reflog entries will be written to indicate movement
    of these refs.

    The original ``ref`` is untouched.

    Subsequent invocations of this function will perform an incremental
    conversion and only convert commits introduced since the last conversion.

    ``exclude_dirs`` is an iterable of directories to exclude from history.

    ``summary_prefix`` allows prefixing the summary line of the commit message
    with a string. A space separates the prefix from the original message.

    ``reviewable_key`` if set will replace Reviewable.io Markdown in the
    commit message with a string of the form ``<reviewable_key>: <URL>``.

    ``remove_reviewable`` will remove Reviewable.io Markdown in the commit
    message.

    ``source_repo_key`` and ``source_repo`` rewrite the commit message to
    contain metadata listing the source repository in the form
    ``<source_repo_key>: <source_repo>``. ``source_repo`` should presumably
    be a URL.

    ``source_revision_key`` if specified will rewrite the commit message
    to contain a line of the form ``<source_revision_key>: COMMIT`` where
    ``COMMIT`` is the original Git commit ID.

    ``committer_action`` specifies how to handle the ``committer`` field in
    the Git commit object. Possible values are ``keep`` (the default) to
    not modify the field, ``use-author`` to copy the ``author`` field to the
    ``committer`` field, or ``use-committer`` to copy the ``committer`` field
    to the ``author`` field.

    ``author_map`` is a dict mapping old author/committer values to new
    ones.

    ``use_p2_author`` indicates whether to use the author of the 2nd parent
    on merge commits. By default, the author of the merge commit is used.

    Returns a dict describing what rewrites were performed. The dict has the
    following keys:

    source_commit
        Git commit hash corresponding to ``ref``.
    dest_commit
        The converted commit hash corresponding to converted ``ref``.
    commit_map
        Dict mapping old commit IDs to converted commit IDs. Only contains
        commits that were converted as part of this evaluation.
    source_ref
        The ref holding the original commit that was last converted (points
        to ``source_commit``).
    dest_ref
        The ref holding the converted commit that was last converted (points
        to ``dest_commit``).
    """
    if committer_action not in ('keep', 'use-author', 'use-committer'):
        raise ValueError('committer_action must be one of keep, use-author, '
                         'or use-committer')

    author_map = author_map or {}

    repo = dulwich.repo.Repo(git_repo)
    head = repo[b'refs/%s' % ref].id

    # Look for state from previous conversion.
    source_ref = b'refs/convert/source/%s' % ref
    dest_ref = b'refs/convert/dest/%s' % ref

    if source_ref in repo.refs and dest_ref not in repo.refs:
        raise Exception('convert source ref without dest ref %s' % dest_ref)
    if dest_ref in repo.refs and source_ref not in repo.refs:
        raise Exception('convert dest ref without source ref %s' % source_ref)

    try:
        source_commit_id = repo[source_ref].id
    except KeyError:
        source_commit_id = None

    try:
        dest_commit_id = repo[dest_ref].id
    except KeyError:
        dest_commit_id = None

    result = {
        'source_commit': head,
        'dest_commit': dest_commit_id,
        'commit_map': {},
        'source_ref': source_ref,
        'dest_ref': dest_ref,
    }

    # Walk the p1 ancestry to find commits to convert, stopping when we found
    # the commit that was converted last. On first run, this will walk all the
    # way to a root commit.
    #
    # This walk also verifies the last converted commit is in the ancestry.
    # If it isn't, a force push / reset has occurred. While we could support
    # non-fast-forward conversions, we choose not to at this time.
    source_commits = []
    commit = repo[head]
    source_commit_found = False
    while True:
        if commit.id == source_commit_id:
            source_commit_found = True
            break

        source_commits.append(commit)

        if not commit.parents:
            break

        commit = repo[commit.parents[0]]

    if source_commit_id and not source_commit_found:
        raise RewriteError('source commit %s not found in ref %s; refusing to '
                           'convert non-fast-forward history' % (
                           source_commit_id, ref))

    if not source_commits:
        logger.warn('no new commits to linearize; not doing anything')
        return result

    source_commits = list(reversed(source_commits))

    logger.warn('linearizing %d commits from %s (%s to %s)' % (
        len(source_commits), ref, source_commits[0].id, source_commits[-1].id))

    github_client = None
    if github_username and github_token:
        github_client = github3.login(username=github_username,
                                      token=github_token)

    github_org, github_repo = None, None
    github_cache_dir = os.path.join(git_repo, 'github-cache')

    if source_repo and source_repo.startswith(b'https://github.com/'):
        orgrepo = source_repo[len(b'https://github.com/'):]
        github_org, github_repo = orgrepo.split(b'/')

    if github_client and github_repo and not os.path.exists(github_cache_dir):
        os.mkdir(github_cache_dir)

    for i, source_commit in enumerate(source_commits):
        logger.warn('%d/%d %s %s' % (
            i + 1, len(source_commits), source_commit.id,
            source_commit.message.splitlines()[0].decode('utf-8', 'replace')))

        dest_commit = source_commit.copy()

        # If we're pruning directories, we need to rewrite tree objects.
        if exclude_dirs:
            dest_commit.tree = prune_directories(repo.object_store,
                                                 dest_commit.tree,
                                                 exclude_dirs).id

        if use_p2_author and len(source_commit.parents) == 2:
            c = repo[source_commit.parents[1]]
            author = c.author
            committer = c.committer
        else:
            author = source_commit.author
            committer = source_commit.committer

        # Replace parents list with our single parent from the last conversion.
        dest_commit.parents = [dest_commit_id] if dest_commit_id else []

        dest_commit.author = author_map.get(author, author)
        dest_commit.committer = author_map.get(committer, committer)

        if committer_action == 'use-author':
            dest_commit.committer = dest_commit.author
            dest_commit.commit_time = dest_commit.author_time
            dest_commit.commit_timezone = dest_commit.author_timezone
        elif committer_action == 'use-committer':
            dest_commit.author = dest_commit.committer
            dest_commit.author_time = dest_commit.commit_time
            dest_commit.author_timezone = dest_commit.commit_timezone
        else:
            assert committer_action == 'keep'

        # Basic commit message rewriting.
        # TODO consider factoring this into a callback to make it extensible.
        if summary_prefix or reviewable_key or remove_reviewable or normalize_github_merge_message:
            message_result = rewrite_commit_message(
                dest_commit.message,
                summary_prefix=summary_prefix,
                reviewable_key=reviewable_key,
                remove_reviewable=remove_reviewable,
                normalize_github_merge=normalize_github_merge_message,
                github_client=github_client,
                github_org=github_org,
                github_repo=github_repo,
                github_cache_dir=github_cache_dir,
            )

            dest_commit.message = message_result['message']

        # Record source repository and revision annotations in commit message
        # if requested.
        if source_repo_key or source_revision_key:
            lines = dest_commit.message.rstrip().splitlines()

            # Insert a blank line if previous line isn't a "metadata" line.
            if not re.match('^[a-zA-Z-]+: \S+$', lines[-1]) or len(lines) == 1:
                lines.append(b'')

            if source_repo_key:
                lines.append(b'%s: %s' % (source_repo_key, source_repo))
            if source_revision_key:
                lines.append(b'%s: %s' % (source_revision_key,
                                          source_commit.id))

            dest_commit.message = b'%s\n' % b'\n'.join(lines)

        # Our commit object is fully transformed. Write it.
        repo.object_store.add_object(dest_commit)

        dest_commit_id = dest_commit.id
        result['commit_map'][source_commit.id] = dest_commit_id

    result['dest_commit'] = dest_commit_id

    # Store refs to the converted source and dest commits. We use
    # ``git update-ref`` so reflogs are written (Dulwich doesn't appear
    # to write reflogs).
    reflog_commands = []
    if source_ref in repo:
        reflog_commands.append(b'update %s\0%s\0%s' % (
            source_ref, head, repo[source_ref].id))
    else:
        reflog_commands.append(b'create %s\0%s' % (source_ref, head))

    if dest_ref in repo:
        reflog_commands.append(b'update %s\0%s\0%s' % (
            dest_ref, dest_commit_id, repo[dest_ref].id))
    else:
        reflog_commands.append(b'create %s\0%s' % (dest_ref, dest_commit_id))

    p = subprocess.Popen([b'git', b'update-ref',
                          b'--create-reflog',
                          b'-m', b'linearize %s' % ref,
                          b'--stdin', b'-z'],
                         stdin=subprocess.PIPE,
                         cwd=git_repo)
    p.stdin.write(b'\0'.join(reflog_commands))
    p.stdin.close()
    res = p.wait()
    if res:
        raise Exception('failed to update refs')

    logger.warn('%s converted; original: %s; rewritten: %s' % (
                ref, head, repo[dest_ref].id))

    # Perform a garbage collection so we don't have potentially thousands
    # of loose objects sitting around, as performance will suffer and Git
    # will complain otherwise.
    subprocess.check_call([b'git',
                           b'-c', b'gc.autodetach=false',
                           b'gc', b'--auto'], cwd=git_repo)

    return result
