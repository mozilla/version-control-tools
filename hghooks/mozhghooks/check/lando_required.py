# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import re
import os

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)

from mercurial import (
    demandimport,
    pycompat,
)

from hgmolib.ldap_helper import get_active_scm_groups

MAGIC_WORDS = b"MANUAL PUSH:"
MAGICWORDS_WITH_JUSTIFICATION_RE = re.compile(
    br".*(%s)\s*(.+)" % re.escape(MAGIC_WORDS)
)

ACTIVE_SCM_ALLOW_DIRECT_PUSH = "active_scm_allow_direct_push"

ACTIVE_SCM_LEVEL_3 = "active_scm_level_3"

SENTRY_LOG_MESSAGE = (
    b'%(user)s pushed: "%(justification)s". (%(repo)s@%(node)s, %(scm_level)s)'
)

SUBMIT_BUGZILLA_URL = b"<https://mzl.la/2HX9Te2>"

SCM_LEVEL_3_PUSH_ERROR_MESSAGE = (
    b"Pushing directly to this repo is disallowed, please use Lando.\n"
    b'To override, in your head commit, include the literal string, "%s",\n'
    b"followed by a sentence of justification."
) % MAGIC_WORDS

SENTRY_FAILURE_WARNING_MESSAGE = (
    b"WARNING: connecting or pushing to Sentry has failed, reporting:\n"
    b"LandoRequiredCheck: %%s\n"
    b"Please report this message by filing a bug at %s.\n"
    b"You do NOT need to retry as a result of this error message. Continuing...\n"
) % SUBMIT_BUGZILLA_URL

LDAP_USER_FAILURE_MESSAGE = (
    b"Unable to retrieve LDAP information about you, therefore we cannot allow\n"
    b"your push to proceed. This is a fatal error.\n"
    b"You may retry your push in the hopes that this a transient problem.\n"
    b"If this problem persists, please report this error by filing a bug at %s\n"
) % SUBMIT_BUGZILLA_URL

LDAP_USER_EXCEPTION_FAILURE_MESSAGE = (
    b"%s" b"Please include this information in your bug submission:\n%%s"
) % LDAP_USER_FAILURE_MESSAGE

INSUFFICIENT_PRIVILEGE_FAILURE_MESSAGE = (
    b"You do not have sufficient privilege to push to this repo.\n"
)

INTERNAL_ERROR_MESSAGE = (
    b"An internal error has prevented you from successfully pushing.\n"
    b"You may retry your push in the hopes that this a transient problem.\n"
    b"If this problem persists, please report this error by filing a bug at %s\n"
    b'Include "LandoRequiredCheck: invalid privilege_level" in your error report\n'
) % SUBMIT_BUGZILLA_URL

REV_URL = 'https://hg.mozilla.org/%(repo)s/rev/%(rev)s'


def get_user_and_group_affiliations():
    """Determine the user_name and fetch any group affiliations from some authority.
    The default implementation is LDAP."""
    user_name = os.environ.get("USER", None)
    if not user_name:
        return None, []
    return user_name, get_active_scm_groups(user_name)


def get_changeset_justification(description):
    """Test to see if the description has appropriate magic words and justification
    parameters:
        description - a string containing the commit message of the top commit for the push.
                      This string is to contain the magic words and justification
    returns:
        None - the magic words and/or justification are not present in the description
        str - the justification provided for using a manual push
    """
    result = MAGICWORDS_WITH_JUSTIFICATION_RE.search(description)
    if result is None:
        return None

    try:
        _magic_words, justification = result.groups()
        # if further processing become necessary in the future, this is an appropriate location
        # further_acceptance_processing(description, justification)
        return justification
    except ValueError:
        # this is the case when the magic words are present, but the justification is not
        return None


class LandoRequiredCheck(PreTxnChangegroupCheck):

    @property
    def name(self):
        return b"lando_required"

    def relevant(self):
        lando_required_list = self.ui.config(b"mozilla", b"lando_required_repo_list")
        if not lando_required_list:
            return False

        target_repo_names = (
            x.strip()
            for x in lando_required_list.split(b",")
        )

        self.repo_name = self.repo.root.replace(b"/repo/hg/mozilla/", b"", 1)
        return self.repo_name in target_repo_names

    def _log_push_attempt(self, event_message):
        """send an event message to Sentry
        parameters:
            event_message - a string with the text of the event message
        """
        sentry_dsn = self.ui.config(b"mozilla", b"sentry_dsn")
        if not sentry_dsn:
            # the sentry_dsn was an empty string - write to stdout instead of using sentry
            self.ui.write(b"%s\n" % event_message)
            return

        # `sentry_sdk` doesn't like the demandimporter. Deactivate it,
        # and only import when we need to ping Sentry.
        with demandimport.deactivated():
            import sentry_sdk

        try:
            sentry_sdk.init(sentry_dsn)

            with sentry_sdk.push_scope() as scope:
                scope.user = {'username': self.user_name}
                scope.set_tag('repo', self.repo_name)
                scope.set_tag('scm_level', self.privilege_level)
                scope.set_extra('changeset', self.head)
                scope.set_extra('justification', self.justification)
                scope.set_extra('url', REV_URL % {
                    'repo': self.repo_name,
                    'rev': self.head,
                })

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
                self.ui, b"warning", SENTRY_FAILURE_WARNING_MESSAGE % pycompat.bytestr(e)
            )

    def pre(self, node):
        # `privilege_level` has only three allowable states: None, ACTIVE_SCM_ALLOW_DIRECT_PUSH, and
        # ACTIVE_SCM_LEVEL_3.
        self.privilege_level = None
        self.head = None
        self.justification = None
        try:
            # The hit on LDAP should only happen once at the beginning of the check process.
            # `pre` is the only opportunity to do so before the iteration through the
            # commits in the changegroup by the `check` method.
            self.user_name, self.user_groups = get_user_and_group_affiliations()
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
                self.ui, b"error", LDAP_USER_EXCEPTION_FAILURE_MESSAGE % pycompat.bytestr(e)
            )
            return
        if not self.user_groups:
            # Since this method `pre` cannot react to fatal errors, the `None` value in
            # `privilege_level` will abort this check in the future call to method `check`
            print_banner(self.ui, b"error", LDAP_USER_FAILURE_MESSAGE)
            return
        if ACTIVE_SCM_ALLOW_DIRECT_PUSH in self.user_groups:
            self.privilege_level = ACTIVE_SCM_ALLOW_DIRECT_PUSH
        elif ACTIVE_SCM_LEVEL_3 in self.user_groups:
            self.privilege_level = ACTIVE_SCM_LEVEL_3
        else:
            # neither ACTIVE_SCM_ALLOW_DIRECT_PUSH nor ACTIVE_SCM_LEVEL_3
            # Since this method `pre` cannot react to fatal errors, the `None` value in
            # `privilege_level` will abort this check in the future call to method `check`
            print_banner(self.ui, b"error", INSUFFICIENT_PRIVILEGE_FAILURE_MESSAGE)

    def check(self, ctx):
        """This method is called once for each of the commits within the changegroup
        in this push:
            ctx - a single commit from the stack of changesets
        returns:
            False - the tests fail and the push should be disallowed
            True - the tests succeed and the push should be accepted
        """
        if self.privilege_level not in {ACTIVE_SCM_ALLOW_DIRECT_PUSH, ACTIVE_SCM_LEVEL_3, None}:
            # this is some bad internal state where `privilege_level` is outside its allowed values.
            print_banner(self.ui, b"error", INTERNAL_ERROR_MESSAGE)
            return False

        if self.privilege_level is None:
            return False

        self.head = ctx.hex()

        if self.privilege_level == ACTIVE_SCM_ALLOW_DIRECT_PUSH:
            return True

        # Level is active_scm_level_3
        if len(ctx.children()) != 0:
            # this isn't the last commit in the changegroup. Just accept it.
            return True

        # This is the last commit within a collection of changesets
        # Test it for inclusion of MAGIC_WORDS and justification
        self.justification = get_changeset_justification(ctx.description())
        if self.justification:
            return True

        print_banner(self.ui, b"error", SCM_LEVEL_3_PUSH_ERROR_MESSAGE)
        return False

    def post_check(self):
        if self.privilege_level not in {ACTIVE_SCM_ALLOW_DIRECT_PUSH, ACTIVE_SCM_LEVEL_3}:
            # this is some bad internal state. At this point, `privilege_level` should have only been
            # one of the two allowed values above.  Getting to this point indicates an unexpected value
            # that should not happen.  Give an appropriate error message and abort.
            print_banner(self.ui, b"error", INTERNAL_ERROR_MESSAGE)
            return False

        # We don't want notifications for scm_allow_direct_push
        if self.privilege_level == ACTIVE_SCM_ALLOW_DIRECT_PUSH:
            return True

        message = SENTRY_LOG_MESSAGE % {
            b'justification': self.justification,
            b'node': self.head[:12],
            b'repo': self.repo_name,
            # Fields from LDAP need conversion to byte strings
            b'scm_level': pycompat.bytestr(self.privilege_level.upper()),
            b'user': pycompat.bytestr(self.user_name),
        }
        self._log_push_attempt(message)
        return True

