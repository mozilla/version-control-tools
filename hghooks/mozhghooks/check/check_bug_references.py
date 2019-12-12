# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import
import json

from mozautomation import commitparser

from mercurial import (
    pycompat,
    urllibcompat,
)

from ..checks import (
    PreTxnChangegroupCheck,
    print_banner,
)

BUGZILLA_API_BASE_URL = b"https://bugzilla.mozilla.org/rest"
HEADERS = {b"User-Agent": b"bmo-api-client/vct-checks/0.1"}
OVERRIDE_FLAG = b"SKIP_BMO_CHECK"

OVERRIDE_INSTRUCTIONS = (
    b"""
To push this commit anyway and ignore this warning, include %s
in your commit message.
"""
    % OVERRIDE_FLAG
)

OVERRIDE_WARNING = b"""
You have chosen to ignore or skip checking bugs IDs referenced in your commit
message. Security bugs or invalid bugs referenced will not block your push.
"""

ERROR_MESSAGE_NOT_FOUND = b"""
Your commit message references a bug that does not exist. Please check your
commit message and try again.

    Affected bug: %s

%s
"""

ERROR_MESSAGE_UNAUTHORIZED = b"""
Your commit message references bugs that are currently private. To avoid
disclosing the nature of these bugs publicly, please remove the affected bug ID
from the commit message.

    Affected bug: %s

Visit https://wiki.mozilla.org/Security/Bug_Approval_Process for more
information.

%s
"""

ERROR_MESSAGE_OTHER = b"""
While checking if a bug referenced in your commit message is a security bug, an
error occurred and the bug could not be verified.

    Affected bug: %s

%s
"""

ERROR_MESSAGE_NO_BUGZILLA = b"""
Could not access bugzilla.mozilla.org to check if a bug referenced in your
commit message is a security bug. Please try again later.

%s
"""

ERROR_MESSAGES = {
    b"NO_BUGZILLA": ERROR_MESSAGE_NO_BUGZILLA,
    b"OTHER": ERROR_MESSAGE_OTHER,
    404: ERROR_MESSAGE_NOT_FOUND,
    401: ERROR_MESSAGE_UNAUTHORIZED,
}


def parse_bug_ids(string):
    """
    Parses a given string of a commit message into a set of bug IDs.

    Args:
        string (str): the string representing the commit message

    Returns:
        set of bytes: a set of strings representing bug IDs
    """
    return {pycompat.bytestr(b) for b in commitparser.parse_bugs(string)}


class BMOAPIClient(object):
    """
    A thin wrapper to communicate via the BMO API for the purposes of hooks.
    """

    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def _get(self, path, params=None):
        """
        Compile a request using given url and params, and send it via a GET
        request to the BMO API.

        Args:
            path (str): the path to a particular resource (e.g. /bug/123456)
            params (tuple): parameters that will be converted to query params

        Returns:
            file: a file-like object representing the response

        Raises:
            HTTPError: if the requested resource can not be accessed
        """
        params = params or {}
        url = self.base_url + path
        if params:
            url += b"?" + urllibcompat.urlreq.urlencode(params)
        request = urllibcompat.urllib2.Request(url)
        for k, v in self.headers.items():
            request.add_header(k, v)
        response = urllibcompat.urlreq.urlopen(request)
        return response

    def search_bugs(self, bug_ids):
        """
        Given an iterable of bug IDs, query the Bugzilla server and return only
        the ones that are valid and accessible.

        Args:
            bug_ids (set of bytes): the set of bug IDs to check

        Returns:
            set of bytes: the set of valid, accessible bugs
        """
        url = b"/bug"
        params = (
            (b"id", b",".join(sorted(list(bug_ids)))),
            (b"include_fields", b"id"),
        )
        data = json.load(self._get(url, params))
        bugs = data.get(b"bugs", [])
        return {pycompat.bytestr(b["id"]) for b in bugs}

    def get_status_code_for_bug(self, bug_id):
        """
        Given a particular bug ID, query the Bugzilla API's 'get bug' endpoint
        and return the status code.

        Args:
            bug_id (bytes)

        Returns:
            int: the HTTP status code
        """
        url = b"/bug/" + bug_id
        try:
            code = self._get(url).getcode()
        except urllibcompat.urlerr.httperror as e:
            # code could be 400, 401, 404, or possibly another server error
            code = e.getcode()
        return code


class CheckBugReferencesCheck(PreTxnChangegroupCheck):
    """
    This pre-transaction check iterates through all commits in a given push
    attempt, filters out any bug IDs that are present in any commit messages
    then queries the BMO API to check if any of the bugs are either invalid
    or inaccessible. The check will print out a message to the user indicating
    what they should do to fix the problem.

    Attributes:
        bug_ids (set of bytes): bugs IDs collected from all commit messages
        bmo_client (BMOAPIClient): a wrapper to communicate with the BMO API
        _skip_check:
            A flag normally passed via a commit message to skip validating
            bugs against the BMO API.
    """

    @property
    def name(self):
        return b"check_bug_references_check"

    def pre(self, node):
        """
        Initialize the check with an empty set of bug_ids.
        """
        self.bug_ids = set()
        self.bmo_client = BMOAPIClient(BUGZILLA_API_BASE_URL, HEADERS)
        self._skip_check = False

    def relevant(self):
        """
        Checks if the destination repository should be checked or not.
        """
        repos_to_check = self.ui.configlist(
            b"mozilla", b"check_bug_references_repos", default=None
        )
        if repos_to_check:
            return self.repo_metadata[b"path"] in repos_to_check
        return False

    def check(self, ctx):
        """
        Check the current commit's message and add any bug IDs to self.bug_ids.
        Always returns True as the full check will occur in `post_check`.

        This check skips over bugs that are not in draft phase.
        """
        if ctx.phasestr() != b"draft":
            return True

        commit_message = ctx.description()
        if OVERRIDE_FLAG in commit_message:
            self._skip_check = True

        self.bug_ids |= parse_bug_ids(commit_message)
        return True

    def post_check(self):
        """
        If any bug IDs are detected in the commit checks, first search for all
        the bug IDs on BMO API. If none are filtered out, this means that all
        the bug IDs are valid. If any IDs are filtered out, check the first ID
        that is excluded and print a relevant message.
        """
        if not self.bug_ids:
            return True

        if self.bug_ids and self._skip_check:
            # TODO: improve this check so that it provides a more specific
            # warning (e.g. security bugs were found but ignored, etc...)
            print_banner(self.ui, b"warning", OVERRIDE_WARNING)
            return True

        try:
            found_bugs = self.bmo_client.search_bugs(self.bug_ids)
        except (urllibcompat.urlerr.httperror, urllibcompat.urlerr.urlerror):
            print_banner(
                self.ui,
                b"error",
                ERROR_MESSAGES[b"NO_BUGZILLA"] % OVERRIDE_INSTRUCTIONS,
            )
            return False

        invalid_bugs = self.bug_ids - found_bugs
        if not invalid_bugs:
            return True

        # Check a single bug only.
        bug = invalid_bugs.pop()
        try:
            status_code = self.bmo_client.get_status_code_for_bug(bug)
        except urllibcompat.urlerr.urlerror:
            print_banner(
                self.ui,
                b"error",
                ERROR_MESSAGES[b"NO_BUGZILLA"] % OVERRIDE_INSTRUCTIONS,
            )
            return False

        if status_code in (401, 404):
            message = ERROR_MESSAGES[status_code] % (bug, OVERRIDE_INSTRUCTIONS)
        else:
            message = ERROR_MESSAGES[b"OTHER"] % (bug, OVERRIDE_INSTRUCTIONS)
        print_banner(self.ui, b"error", message)
        return False
