# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Shared Mercurial code related to authentication."""

from mercurial import util
from mercurial.i18n import _


class BugzillaAuth(object):
    """Holds Bugzilla authentication credentials."""

    def __init__(self, userid=None, cookie=None, username=None, password=None):
        if userid:
            self._type = 'cookie'
        else:
            self._type = 'explicit'

        self.userid = userid
        self.cookie = cookie
        self.username = username
        self.password = password

def getbugzillaauth(ui, require=False):
    """Obtain Bugzilla authentication credentials from any possible source.

    This returns a BugzillaAuth instance on success or None on failure.

    TODO: Incorporate bzexport's code for grabbing credentials from Firefox
    profiles.
    """

    username = ui.config('bugzilla', 'username')
    password = ui.config('bugzilla', 'password')

    if username and password:
        return BugzillaAuth(username=username, password=password)

    ui.warn(_('tip: to not prompt for Bugzilla credentials in the future, '
              'store them in your hgrc under bugzilla.username and '
              'bugzilla.password\n'))

    if not username:
        username = ui.prompt(_('Bugzilla username'), None)

    if not password:
        password = ui.getpass(_('Bugzilla password'), None)

    if username and password:
        return BugzillaAuth(username=username, password=password)

    if require:
        raise util.Abort(_('unable to obtain Bugzilla authentication.'))

    return None
