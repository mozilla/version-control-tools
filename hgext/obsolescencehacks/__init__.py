# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Change behavior of obsolescence."""

import os
import pwd

from mercurial import (
    configitems,
    error,
    obsolete,
    pycompat,
    registrar,
)

testedwith = b'4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1 5.2'
minimumhgversion = b'4.4'


configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'obshacks', b'obsolescenceexchangeusers',
           default=configitems.dynamicdefault)
configitem(b'obshacks', b'userfromenv',
           default=configitems.dynamicdefault)


def enableevolutionexchange(repo):
    """Enable obsolescence markers exchange if conditions are met."""
    ui = repo.ui

    # Nothing to do if obsolescence isn't enabled at all.
    opts = (obsolete.createmarkersopt, obsolete.allowunstableopt, obsolete.exchangeopt)
    if not any(obsolete.isenabled(repo, opt) for opt in opts):
        return

    features = set(ui.configlist(b'experimental', b'evolution'))
    # Nothing to do if already enabled.
    if b'all' in features or obsolete.exchangeopt in features:
        return

    # Enable exchange if the current user is in the allow list.
    exchangeusers = ui.configlist(b'obshacks', b'obsolescenceexchangeusers', [])
    if not exchangeusers:
        return

    # Some tests can't change the uid, so allow a test mode where the user
    # comes from USER.
    if ui.configbool(b'obshacks', b'userfromenv', False):
        user = ui.environ.get(b'USER')
    else:
        try:
            user = pycompat.bytestr(pwd.getpwuid(os.getuid()).pw_name)
        except KeyError:
            raise error.Abort(b'unable to resolve process user name')

    if user not in exchangeusers:
        return

    evolution = ui.config(b'experimental', b'evolution')
    evolution += b' %s' % obsolete.exchangeopt
    ui.setconfig(b'experimental', b'evolution', evolution.strip(),
                 source=b'obshacksext')


def reposetup(ui, repo):
    enableevolutionexchange(repo)
