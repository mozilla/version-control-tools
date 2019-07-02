#!/usr/bin/env python

# Copyright (C) 2012 Mozilla Foundation
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import absolute_import

import re
import os

from mercurial import registrar
from ..checks import PreTxnChangegroupCheck, print_banner

import sentry_sdk

from hgmolib.ldap_helper import get_active_scm_groups


class PriviligedPushCheck(PreTxnChangegroupCheck):

    MAGIC_WORDS = "PRIVILEGED PUSH:"
    MAGICWORDS_WITH_JUSTIFICATION_RE = re.compile(
        r".*(%s)\s*(.+)" % re.escape(MAGIC_WORDS)
    )

    ACTIVE_SCM_ALLOW_DIRECT_PUSH = "active_scm_allow_direct_push"
    ACTIVE_SCM_LEVEL_3 = "active_scm_level_3"

    SUCCESS_FOR_SCM_ALLOW_DIRECT_PUSH_LOG_MESSAGE = (
        "Successful push: %s by %s (ACTIVE_SCM_ALLOW_DIRECT_PUSH)"
    )
    SUCCESS_FOR_SCM_LEVEL_3_LOG_MESSAGE = (
        "Successful push: %s by %s (ACTIVE_SCM_LEVEL_3)"
    )

    SUBMIT_BUGZILLA_URL = "<https://mzl.la/2HX9Te2>"

    SCM_LEVEL_3_PUSH_ERROR_MESSAGE = (
        "Pushing directly to this repo is disallowed, please use Lando.\n"
        'To override, in your top commit, include the literal string, "%s",\n'
        "followed by a sentence of justification."
    ) % MAGIC_WORDS
    SENTRY_FAILURE_WARNING_MESSAGE = (
        "WARNING: connecting or pushing to Sentry has failed, reporting:\n"
        "PriviligedPushHook: %%s\n"
        "Please report this message by filing a bug at %s.\n"
        "You do NOT need to retry as a result of this error message. Continuing...\n"
    ) % SUBMIT_BUGZILLA_URL
    LDAP_USER_FAILURE_MESSAGE = (
        "Unable to retrieve LDAP information about you, therefore we cannot allow\n"
        "your push to proceed. This is a fatal error.\n"
        "You may retry your push in the hopes that this a transient problem.\n"
        "If this problem persists, please report this error by filing a bug at %s\n"
    ) % SUBMIT_BUGZILLA_URL
    LDAP_USER_EXCEPTION_FAILURE_MESSAGE = (
        "%s" "Please include this information in your bug submission:\n%%s"
    ) % LDAP_USER_FAILURE_MESSAGE
    INSUFFICIENT_PRIVILEGE_FAILURE_MESSAGE = (
        "You do not have sufficient privilege to push to this repo.\n"
    )
    INTERNAL_ERROR_MESSAGE = (
        "An internal error has prevented you from successfully pushing.\n"
        "You may retry your push in the hopes that this a transient problem.\n"
        "If this problem persists, please report this error by filing a bug at %s\n"
        'Include "PrivilegedPushCheck: invalid privilege_level" in your error report\n'
    ) % SUBMIT_BUGZILLA_URL

    @property
    def name(self):
        return "privileged_push"

    def relevant(self):
        target_repo_names = (
            x.strip()
            for x in self.ui.config("mozilla", "priviliged_push_repo_list").split(",")
        )
        repo_name = self.repo.root.replace("/repo/hg/mozilla/", "", 1)
        return repo_name in target_repo_names

    def _log_push_attempt(self, event_message):
        """send an event message to Sentry
        parameters:
            event_message - a string with the text of the event message
        """
        if self.ui.config("mozilla", "sentry_dsn"):
            try:
                sentry_sdk.init(self.ui.config("mozilla", "sentry_dsn"))
                sentry_sdk.capture_message(event_message)
            except Exception as e:
                # The Sentry Documentation does not mention any exceptions that it could raise.
                # Inspection of the unified sentry-sdk source code shows that Sentry does not define
                # an exception hierarchy of its own. Therefore, we cannot predict what exceptions
                # might be raised during the connection and reporting phases: we have no choice but
                # to capture all exceptions.
                # If connecting to Sentry or reporting via Sentry fails, we do not want to derail the
                # users' intent on pushing.  We have nowhere to log the failure, so we notify the
                # user with a warning and proceed as if nothing bad had happened.
                print_banner(
                    self.ui, "warning", self.SENTRY_FAILURE_WARNING_MESSAGE % repr(e)
                )
        else:
            # the sentry_dsn was an empty string - write to stdout instead of using sentry
            self.ui.write("%s\n" % event_message)

    def _get_user_and_group_affiliations(self):
        """determine the user_name and fetch any group affiliations from some authority.
        The default implementation is LDAP."""
        user_name = os.environ.get("USER", None)
        if not user_name:
            return None, []
        return user_name, get_active_scm_groups(user_name)

    def _has_justification(self, description):
        """Test to see if the description has appropriate magic words and justification
        parameters:
            description - a string containing the commit message of the top commit for the push.
                          This string is to contain the magic words and justification
        returns:
            False - the magic words and/or justification are not present in the description
            True - the magic words and justification are present and acceptable
        """
        result = self.MAGICWORDS_WITH_JUSTIFICATION_RE.search(description)
        if result is None:
            return False
        try:
            some_magic_words, justification = result.groups()
            # if further processing become necessary in the future, this is an appropriate location
            # further_acceptance_processing(description, justification)
            return True
        except ValueError:
            # this is the case when the magic words are present, but the justification is not
            return False

    def pre(self, node):
        # `privilege_level` has only three allowable states: None, ACTIVE_SCM_ALLOW_DIRECT_PUSH, and
        # ACTIVE_SCM_LEVEL_3.
        self.privilege_level = None
        self.first_ctx_rev = None
        try:
            # The hit on LDAP should only happen once at the beginning of the check process.
            # `pre` is the only opportunity to do so before the iteration through the
            # commits in the changegroup by the `check` method.
            self.user_name, self.user_groups = self._get_user_and_group_affiliations()
        except Exception as e:
            # The `_get_user_and_group_affiliations` method has raised an unexpected exception.
            # It is not likely an LDAP connection error because the `get_active_scm_groups` method
            # suppresses all LDAP exceptions in favor of logging to stderr and returning None.
            # However,`get_active_scm_groups` does have other opportunities to raise exceptions that
            # have not been suppressed. As we have no user information at this point, we cannot
            # let the push proceed.
            # Since this method `pre` cannot react to fatal errors, the `None` value in
            # `privilege_level` will abort this check in the future call to method `check`
            print_banner(
                self.ui, "error", self.LDAP_USER_EXCEPTION_FAILURE_MESSAGE % repr(e)
            )
            return
        if not self.user_groups:
            # Since this method `pre` cannot react to fatal errors, the `None` value in
            # `privilege_level` will abort this check in the future call to method `check`
            print_banner(self.ui, "error", self.LDAP_USER_FAILURE_MESSAGE)
            return
        if self.ACTIVE_SCM_ALLOW_DIRECT_PUSH in self.user_groups:
            self.privilege_level = self.ACTIVE_SCM_ALLOW_DIRECT_PUSH
        elif self.ACTIVE_SCM_LEVEL_3 in self.user_groups:
            self.privilege_level = self.ACTIVE_SCM_LEVEL_3
        else:
            # neither ACTIVE_SCM_ALLOW_DIRECT_PUSH nor ACTIVE_SCM_LEVEL_3
            # Since this method `pre` cannot react to fatal errors, the `None` value in
            # `privilege_level` will abort this check in the future call to method `check`
            print_banner(self.ui, "error", self.INSUFFICIENT_PRIVILEGE_FAILURE_MESSAGE)

    def check(self, ctx):
        """This method is called once for each of the commits within the changegroup
        in this push:
            ctx - a single commit from the stack of changesets
        returns:
            False - the tests fail and the push should be disallowed
            True - the tests succeed and the push should be accepted
        """
        if self.privilege_level is None:
            return False
        if self.first_ctx_rev is None:
            self.first_ctx_rev = ctx.hex()[:12]
        if self.privilege_level is self.ACTIVE_SCM_ALLOW_DIRECT_PUSH:
            return True
        if self.privilege_level is self.ACTIVE_SCM_LEVEL_3:
            # MAGIC_WORDS and a justification must be in the last commit in the changesetgroup
            if len(ctx.children()) == 0:
                # This is the last commit within a collection of changesets
                # Test it for inclusion of MAGIC_WORDS and justification
                if self._has_justification(ctx.description()):
                    return True
                print_banner(self.ui, "error", self.SCM_LEVEL_3_PUSH_ERROR_MESSAGE)
                return False
            # this isn't the last commit in the changegroup. Just accept it.
            return True
        # this is some bad internal state where `privilege_level` is outside its allowed values.
        print_banner(self.ui, "error", self.INTERNAL_ERROR_MESSAGE)
        return False

    def post_check(self):
        if self.privilege_level is self.ACTIVE_SCM_ALLOW_DIRECT_PUSH:
            self._log_push_attempt(
                self.SUCCESS_FOR_SCM_ALLOW_DIRECT_PUSH_LOG_MESSAGE
                % (self.first_ctx_rev, self.user_name)
            )
            return True
        if self.privilege_level is self.ACTIVE_SCM_LEVEL_3:
            self._log_push_attempt(
                self.SUCCESS_FOR_SCM_LEVEL_3_LOG_MESSAGE
                % (self.first_ctx_rev, self.user_name)
            )
            return True
        # this is some bad internal state. At this point, `privilege_level` should have only been
        # one of the two allowed values above.  Getting to this point indicates an unexpected value
        # that should not happen.  Give an appropriate error message and abort.
        print_banner(self.ui, "error", self.INTERNAL_ERROR_MESSAGE)
        return False
