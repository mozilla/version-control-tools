# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Change behavior of obsolescence."""

import os
import pwd

from mercurial import (
    configitems,
    error,
    obsolete,
    registrar,
)

testedwith = '4.4 4.5 4.6'
minimumhgversion = '4.4'


configtable = {}
configitem = registrar.configitem(configtable)

configitem('obshacks', 'obsolescenceexchangeusers',
           default=configitems.dynamicdefault)
configitem('obshacks', 'userfromenv',
           default=configitems.dynamicdefault)


def enableevolutionexchange(repo):
    """Enable obsolescence markers exchange if conditions are met."""
    ui = repo.ui

    # Nothing to do if obsolescence isn't enabled at all.
    opts = (obsolete.createmarkersopt, obsolete.allowunstableopt, obsolete.exchangeopt)
    if not any(obsolete.isenabled(repo, opt) for opt in opts):
        return

    features = set(ui.configlist('experimental', 'evolution'))
    # Nothing to do if already enabled.
    if 'all' in features or obsolete.exchangeopt in features:
        return

    # Enable exchange if the current user is in the allow list.
    exchangeusers = ui.configlist('obshacks', 'obsolescenceexchangeusers', [])
    if not exchangeusers:
        return

    # Some tests can't change the uid, so allow a test mode where the user
    # comes from USER.
    if ui.configbool('obshacks', 'userfromenv', False):
        user = os.environ.get('USER')
    else:
        try:
            user = pwd.getpwuid(os.getuid()).pw_name
        except KeyError:
            raise error.Abort('unable to resolve process user name')

    if user not in exchangeusers:
        return

    evolution = ui.config('experimental', 'evolution')
    evolution += ' %s' % obsolete.exchangeopt
    ui.setconfig('experimental', 'evolution', evolution.strip(),
                 source='obshacksext')


def reposetup(ui, repo):
    enableevolutionexchange(repo)
