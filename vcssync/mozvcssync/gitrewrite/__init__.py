# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, unicode_literals

import collections
import json
import os
import re
import stat
import uuid

import github3.pulls

from ..util import (
    get_github_client,
)


class RewriteError(Exception):
    """Represents an error that occurred during rewriting."""


def prune_directories(object_store, tree_id, directories):
    """Remove directories from a tree, writing the new trees to the store.

    An existing Git Tree object defined by ``tree_id`` will be examined for
    directories in the ``directories`` iterable. If a directory exists, new tree
    objects will be created as necessary.

    The ``dulwich.objects.Tree`` instance for the rewritten tree will be
    returned.
    """
    directories = set(d.strip(b'/') for d in directories)
    assert b'' not in directories

    class TreeDict(collections.defaultdict):
        def __missing__(self, key):
            path = b''
            tree = self[path]
            for d in key.split(b'/'):
                if path:
                    path += b'/%s' % d
                else:
                    path = d

                new_tree = self.get(path)
                if not new_tree:
                    new_tree = object_store[tree[d][1]]
                    self[path] = new_tree

                tree = new_tree

            return tree

    # Our strategy is to iterate directories, find the tree object for its
    # parent directory/tree, then rewrite parent tree objects, if necessary.
    #
    # A cache of path to Tree is maintained so lookups are fast and so we can
    # wait until the end to write any objects.

    # Maps path to possibly rewritten tree.
    trees = TreeDict()
    trees[b''] = object_store[tree_id]
    dirty = set()

    for directory in sorted(directories):
        if b'/' in directory:
            parent_path, basename = directory.rsplit(b'/', 1)
        else:
            parent_path, basename = b'', directory

        # Parent directory doesn't exist.
        try:
            tree = trees[parent_path]
        except KeyError:
            continue

        # This path doesn't exist.
        try:
            entry = tree[basename]
        except KeyError:
            continue

        # Path isn't a directory.
        if not entry[0] & stat.S_IFDIR:
            continue

        # Remove the entry and rewrite parent trees.
        del tree[basename]
        dirty.add(parent_path)

        # Special case where we're already at the root.
        if parent_path == b'':
            continue

        while b'/' in parent_path:
            parent_path, basename = parent_path.rsplit(b'/', 1)
            parent_tree = trees[parent_path]
            parent_tree[basename] = (parent_tree[basename][0], tree.id)
            tree = parent_tree
            dirty.add(parent_path)

        # And handle the root tree.
        parent_tree = trees[b'']
        parent_tree[parent_path] = (entry[0], tree.id)
        dirty.add(b'')

    for t in sorted(dirty, key=len, reverse=True):
        object_store.add_object(trees[t])

    return trees[b'']


RE_REVIEWABLE = re.compile(r'''
<!--\sReviewable:start\s-->
# Fast forward to start of (URL) expression
[^\(]+\(
(?P<url>[^\)]+)
\).*<!--\sReviewable:end\s-->
''', re.DOTALL | re.VERBOSE)


RE_GITHUB_MERGE_PR = re.compile(r'''
^Merge\spull\srequest\s\#(?P<number>\d+)\sfrom\s(?P<where>[^\s]+)
''', re.VERBOSE)


RE_GITHUB_MERGE_PR2 = re.compile(r'''
[aA]uto\smerge\sof\s
\#(?P<number>\d+)
\s[:-]\s
(?P<where>[^,]+),
\sr=(?P<reviewer>[^\s]+)
''', re.VERBOSE)


def rewrite_commit_message(message, summary_prefix=None, reviewable_key=None,
                           remove_reviewable=False,
                           normalize_github_merge=False,
                           github_client=None,
                           github_org=None,
                           github_repo=None,
                           github_cache_dir=None):
    """Rewrite a Git commit message.

    ``summary_prefix`` can prefix the summary line of the commit message
    with a string.

    ``reviewable_key`` replaces Reviewable.io Markdown with a ``<key>: <URL>``
    string.

    ``remove_reviewable`` will remove a Reviewable.io Markdown block.

    ``normalize_github_merge`` will reformat the commit message generated
    by performing a merge in GitHub. It replaces the somewhat uninformative
    "Merge pull request #N" with the pull request title, which is extracted
    from a subsequent line in the commit message.
    """
    if reviewable_key and remove_reviewable:
        raise Exception('cannot specify both reviewable_key and remove_reviewable')

    result = {}

    if remove_reviewable:
        message = RE_REVIEWABLE.sub(b'', message)

    if reviewable_key:
        # We can't plug reviewable_key into sub() because it may contain special
        # characters. So, we replace with a unique value during substitution
        # then do a literal replace.
        unique = str(uuid.uuid1())
        message = RE_REVIEWABLE.sub(b'%s: \\g<url>' % unique, message)
        message = message.replace(unique, reviewable_key)

    def get_summary():
        for i, line in enumerate(message.splitlines()[1:]):
            if line.strip():
                return line, i + 1

        return None, None

    def get_user(login):
        if github_cache_dir:
            path = os.path.join(github_cache_dir, 'user-%s.json' % login)

            if os.path.exists(path):
                with open(path, 'rb') as fh:
                    data = json.load(fh, encoding='utf-8')

                return github3.users.User(data, github_client)

        if github_client:
            user = github_client.user(login)
            if user and github_cache_dir:
                with open(path, 'wb') as fh:
                    json.dump(user.to_json(), fh, encoding='utf-8',
                              indent=2, sort_keys=True,
                              separators=(',', ': '))

            return user

        return None

    def get_pull_request(number):
        pr = None

        if github_cache_dir:
            path = os.path.join(github_cache_dir, 'pr-%s.json' % number)

            if os.path.exists(path):
                with open(path, 'rb') as fh:
                    data = json.load(fh, encoding='utf-8')

                pr = github3.pulls.PullRequest(data, github_client)

        if not pr and github_client and github_org and github_repo:
            pr = github_client.pull_request(github_org, github_repo, number)
            if pr and github_cache_dir:
                with open(path, 'wb') as fh:
                    json.dump(pr.to_json(), fh, encoding='utf-8',
                              indent=2, sort_keys=True,
                              separators=(',', ': '))

        user = None
        if pr and pr.head.user:
            user = get_user(pr.head.user.login)

        return pr, user

    if normalize_github_merge:
        # This is the GitHub default message.
        m = RE_GITHUB_MERGE_PR.match(message)
        if m:
            lines = message.splitlines()

            pr, user = get_pull_request(m.group('number'))
            result['pull_request'] = pr
            result['pull_request_user'] = user

            pr_summary, pr_line = get_summary()
            if pr_summary:
                where = b':'.join(m.group('where').rsplit(b'/', 1))
                summary = b'Merge #%s - %s (from %s)' % (
                    m.group('number'),
                    pr_summary.rstrip().rstrip(b'.'),
                    where)

                message = b'\n'.join([summary] + lines[pr_line + 1:])

        # This convention is used by Servo / Bors.
        m = RE_GITHUB_MERGE_PR2.match(message)
        if m:
            lines = message.splitlines()

            where = m.group('where')
            pr, user = get_pull_request(m.group('number'))
            result['pull_request'] = pr
            result['pull_request_user'] = user
            if pr:
                if pr.head.label:
                    where = pr.head.label.encode('utf-8')

                title = pr.title.encode('utf-8')

                summary = b'Merge #%s - %s (from %s); r=%s' % (
                    m.group('number'),
                    title.rstrip().rstrip(b'.'),
                    where,
                    m.group('reviewer'))

                # Some commits have the PR title as the first non-summary line.
                # If so, remove that line and a blank line that follows.
                if lines[2:4] in ([title, b''], [title]):
                    lines = lines[0:2] + lines[4:]

                message = b'\n'.join([summary] + lines[1:])

            # No GitHub API data. Rely on the commit message itself.
            else:
                pr_summary, pr_line = get_summary()
                if pr_summary:
                    summary = b'Merge #%s - %s (from %s); r=%s' % (
                        m.group('number'),
                        pr_summary.rstrip().rstrip(b'.'),
                        m.group('where'),
                        m.group('reviewer'))
                    message = b'\n'.join([summary] + lines[pr_line + 1:])
                else:
                    summary = b'Merge #%s (from %s); r=%s' % (
                        m.group('number'),
                        m.group('where'),
                        m.group('reviewer'))
                    message = b'\n'.join([summary] + lines[1:])

    if summary_prefix:
        message = b'%s %s' % (summary_prefix, message)

    message = b'%s\n' % message.rstrip()

    assert isinstance(message, str)
    result['message'] = message

    return result


def commit_metadata_rewriter(
        repo,
        summary_prefix=None,
        reviewable_key=None,
        remove_reviewable=False,
        normalize_github_merge_message=False,
        source_repo_key=None,
        source_repo=None,
        source_revision_key=None,
        committer_action='keep',
        author_map=None,
        use_p2_author=False,
        github_token=None):
    """Obtain a function used to rewrite Git commit object metadata.

    The returned function is called with 2 arguments: the old and new Git commit
    objects. The function is expected to mutate the new Git commit object.

    The function is attached to a ``dulwich.repo.Repo`` instance and a set of
    behavioral options  defined via arguments. Those arguments are as follows:

    ``summary_prefix`` allows prefixing the summary line of the commit
    message with a string. A space separates the prefix from the original
    message.

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
    ``committer`` field, or ``use-committer`` to copy the ``committer``
    field to the ``author`` field.

    ``author_map`` is a dict mapping old author/committer values to new
    ones.

    ``use_p2_author`` indicates whether to use the author of the 2nd parent
    on merge commits. By default, the author of the merge commit is used.
    """
    if committer_action not in ('keep', 'use-author', 'use-committer'):
        raise ValueError('committer_action must be one of keep, use-author, '
                         'or use-committer')

    author_map = author_map or {}

    github_client = get_github_client(github_token) if github_token else None
    github_org, github_repo = None, None
    github_cache_dir = os.path.join(repo.path, 'github-cache')

    if source_repo and source_repo.startswith(b'https://github.com/'):
        orgrepo = source_repo[len(b'https://github.com/'):]
        github_org, github_repo = orgrepo.split(b'/')

    if github_client and github_repo and not os.path.exists(github_cache_dir):
        os.mkdir(github_cache_dir)


    def rewrite_commit(source_commit, dest_commit):
        if use_p2_author and len(source_commit.parents) == 2:
            c = repo[source_commit.parents[1]]
            author = c.author
            committer = c.committer
        else:
            author = source_commit.author
            committer = source_commit.committer

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

    return rewrite_commit
