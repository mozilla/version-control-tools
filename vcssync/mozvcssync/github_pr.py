# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Utility functions for performing various GitHub functionality."""

from __future__ import unicode_literals

import logging
import re
import tempfile
import urllib
import urlparse

import github3
from gitutil import GitCommand, setup_local_clone

logger = logging.getLogger(__name__)


class GitHubPR(object):
    """Helper class for creating GitHub pull requests."""

    def __init__(self, auth_token, repo_name, path, github=None):
        assert auth_token

        self.upstream_user, self.repo_name = repo_name.split('/')
        self.repo_path = path
        self.token = auth_token
        self._fork_repo = None
        self._upstream_repo = None

        self.git = GitCommand(path, secret=auth_token)

        # Allow the caller to pass in a different github3.GitHub object
        # (eg. for testing).
        self.github = github or github3.GitHub()

        # Login to GitHub.
        self.github.login(token=self.token)
        self.user = str(self.github.user())

    def fork_repo(self):
        # Returns GitHub repository object for the forked repo (ie. where the
        # pull requests will be created).
        if not self._fork_repo:
            self._fork_repo = self.github.repository(self.user, self.repo_name)
            if self._fork_repo is None:
                raise Exception('failed to find github repo: %s/%s'
                                % (self.user, self.repo_name))
        return self._fork_repo

    def upstream_repo(self):
        # Returns GitHub repository object for the upstream repo (ie. where
        # the pull requests will be landed).
        if not self._upstream_repo:
            self._upstream_repo = self.github.repository(self.upstream_user,
                                                         self.repo_name)
            if self._upstream_repo is None:
                raise Exception('failed to find github repo: %s/%s'
                                % (self.upstream_user, self.repo_name))
        return self._upstream_repo

    @staticmethod
    def _previous_pr(repo, head, state='all'):
        return next(repo.iter_pulls(head=head, state=state), None)

    def pr_from_branch(self, branch_name, state='all'):
        return self._previous_pr(self.upstream_repo(),
                                 '%s:%s' % (self.user, branch_name),
                                 state=state)

    def update_or_create_pr(self, repo, user, branch, title, body,
                            title_multiple=None):
        head = "%s:%s" % (user, branch)

        try:
            # Find existing pull request.
            pr = self._previous_pr(repo, head, state='open')

            if pr:
                logger.info('updating pull request %s' % pr.html_url)
                # This PR may contain multiple different changes.  Update
                # the title to reflect that, and append the new backout to
                # the current PR body.
                pr.update(
                    title=title_multiple or title,
                    body='%s\n\n---\n\n%s' % (pr.body.strip(), body))
            else:
                logger.info('creating pull request against %s'
                            % repo.html_url)
                pr = repo.create_pull(base='master', head=head,
                                      title=title, body=body)
                logger.info('created %s' % pr.html_url)
        except github3.models.GitHubError as e:
            # GitHubError stores the actual response from GitHub in `errors`
            if e.errors:
                messages = []
                for error in e.errors:
                    messages.append(error['message'])

                # If there's only one error, and it's that there were no
                # commits between master and the backout branch, this operation
                # is a NO-OP, but not a failure.
                if (len(messages) == 1 and
                        messages[0].startswith('No commits between ')):
                    logger.warning(messages[0])
                    return None

                raise RuntimeError('%s\n\n%s' % (str(e), '\n'.join(messages)))
            raise RuntimeError(str(e))

        return pr

    def create_pr_from_patch(self,
                             branch_name=None, reset_branch=False,
                             description=None, author=None,
                             pr_title=None, pr_title_multiple=None,
                             pr_body=None,
                             patch_file=None, patch_callback=None):
        """Create a pull request and return the URL to the pull request.

        :param branch_name: Name of the branch to create the pull request in.
            The branch will be created if required.
        :param reset_branch: When True, the branch will be deleted and recreated
            to ensure it is clean prior to PR creation.
        :param description: The commit description for this change.
        :param author: The author of this commit.
        :param pr_title: The title of the pull request.  If not provided the
            first line of the `description` will be used.
        :param pr_title_multiple: The title of a pull request when multiple
            commits are merged.  If not provided the pr_title will be used.
        :param pr_body: The body text of the pull request.  If not provided the
            `description` will be used.
        :param patch_file: Full filename to a patch/diff to be applied.  Cannot
            be set if `patch_callback` is set.
        :param patch_callback: Callback function that will apply changes to
            the git repository.  Called with a single argument of the
            `GitCommand` object.  Cannot be set if `patch_file` is set.
        :return: a github3.PullRequest object, or None if no changes were made.
        """
        assert branch_name is not None
        assert description is not None
        assert author is not None
        assert patch_file is not None or patch_callback is not None
        assert not (patch_file is not None and patch_callback is not None)

        git = self.git

        # Load repos from GitHub.
        fork_repo = self.fork_repo()
        upstream_repo = self.upstream_repo()

        setup_local_clone(self.repo_path, fork_repo.clone_url, git=git)

        # Update master refs.
        git.cmd('fetch', upstream_repo.clone_url,
                '+master:refs/upstream/master')

        # It's simpler to just delete and recreate the branch to reset it.
        if reset_branch and git.get('branch', '--list', branch_name):
            git.cmd('checkout', 'master', '--force')
            git.cmd('branch', '--delete', '--force', branch_name)
            # noinspection PyBroadException
            try:
                git.cmd('push', 'origin', '--delete', branch_name)
            except Exception:
                pass

        # Create/checkout branch.
        git.cmd('checkout', '-B', branch_name)
        git.cmd('clean', '-d', '--force')
        git.cmd('merge', 'refs/upstream/master')

        # Apply changes.
        if patch_file:
            git.cmd('apply', patch_file, '--verbose')
        if callable(patch_callback):
            patch_callback(git)

        # Stage changes.
        git.cmd('add', '--all', '--verbose')

        # If there are no changes staged this means either there's actually
        # nothing changed, or the changes were pushed to github however
        # creation of the PR failed.  Continue to try to create the PR and
        # let github handle an actual "nothing changed" state.

        if git.get('status', '--short'):

            # Commit changes.
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(description.encode('utf-8'))
                temp_file.flush()
                git.cmd('commit',
                        '--file', temp_file.name,
                        '--author', author)

            # Insert user and token into the HTTP auth part of the auth url,
            # which Git will extract and use for authentication.
            u = urlparse.urlsplit(fork_repo.clone_url)
            url = re.sub(r'^//', '', urlparse.urlunsplit(
                ['', u.netloc, u.path, u.query, '']))
            push_auth_url = 'https://%s:%s@%s' % (urllib.quote(self.user),
                                                  urllib.quote(self.token),
                                                  url)

            # Push.
            git.cmd('push', '--force', push_auth_url)

        else:
            logger.warn('No changes to commit/push')

        pr_title = pr_title or description.splitlines()[0]
        pr_body = pr_body or description
        return self.update_or_create_pr(
            upstream_repo, self.user, branch_name, pr_title, pr_body,
            title_multiple=pr_title_multiple)
