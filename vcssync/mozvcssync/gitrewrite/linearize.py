# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Functionality for "linearizing" a Git repository.

This takes a repository with merge commits and rewrites commits to remove
the merges, yielding a clean, linear history.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import subprocess

from . import (
    prune_directories,
    RewriteError,
)
from ..gitutil import (
    update_git_refs,
)


logger = logging.getLogger(__name__)


def linearize_git_repo(repo, ref, exclude_dirs=None,
                       commit_rewriter=None):
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

    ``commit_rewriter`` is a callable that will be invoked for every commit
    being rewritten. The called function can modify the Git commit object
    as it sees fit.

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

    last_tree = repo[dest_commit_id].tree if dest_commit_id else None
    rewrite_count = 0

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

        # If the tree is identical to the last commit, the commit is empty.
        # There is no value in keeping it. So we drop it.
        #
        # In some cases, retaining empty commits may be desirable. So this
        # behavior could be controlled by a function argument if wanted.
        if dest_commit.tree == last_tree:
            logger.warn('dropping %s because no tree changes' %
                        source_commit.id)
            continue

        # Replace parents list with our single parent from the last conversion.
        dest_commit.parents = [dest_commit_id] if dest_commit_id else []

        if commit_rewriter:
            commit_rewriter(source_commit, dest_commit)

        # Our commit object is fully transformed. Write it.
        repo.object_store.add_object(dest_commit)

        rewrite_count += 1
        dest_commit_id = dest_commit.id
        last_tree = dest_commit.tree
        result['commit_map'][source_commit.id] = dest_commit_id

    result['dest_commit'] = dest_commit_id

    # Store refs to the converted source and dest commits. We use
    # ``git update-ref`` so reflogs are written (Dulwich doesn't appear
    # to write reflogs).
    reflog_actions = []
    if source_ref in repo:
        reflog_actions.append(('update', source_ref, head, repo[source_ref].id))
    else:
        reflog_actions.append(('create', source_ref, head))

    if dest_ref in repo:
        reflog_actions.append(('update', dest_ref, dest_commit_id,
                               repo[dest_ref].id))
    else:
        reflog_actions.append(('create', dest_ref, dest_commit_id))

    update_git_refs(repo, b'linearize %s' % ref, *reflog_actions)

    logger.warn('%d commits from %s converted; original: %s; rewritten: %s' % (
                rewrite_count, ref, head, repo[dest_ref].id))

    # Perform a garbage collection so we don't have potentially thousands
    # of loose objects sitting around, as performance will suffer and Git
    # will complain otherwise.
    subprocess.check_call([b'git',
                           b'-c', b'gc.autodetach=false',
                           b'gc', b'--auto'], cwd=repo.path)

    return result
