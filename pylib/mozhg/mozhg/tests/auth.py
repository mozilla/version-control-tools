# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Dummy Mercurial extension to facilitate testing of mozhg.auth.getbugzillaauth()."""

import getpass
import os

from mercurial import (
    cmdutil,
    commands,
)

OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', '..', '..', '..', 'hgext', 'bootstrap.py'))

from mozhg.auth import getbugzillaauth

cmdtable = {}
command = cmdutil.command(cmdtable)
commands.norepo += ' bzauth bzcreatecookie'

@command('bzauth', [
    ('', 'require', False, 'Require auth'),
    ('', 'fakegetpass', '', 'Provide a fake getpass.getpass answer'),
    ], 'hg bzauth')
def bzauth(ui, require=False, fakegetpass=None):
    if fakegetpass:
        def newgetpass(arg):
            return fakegetpass
        getpass.getpass = newgetpass

    a = getbugzillaauth(ui, require=require)
    if a:
        ui.write('userid: %s\n' % a.userid)
        ui.write('cookie: %s\n' % a.cookie)
        ui.write('username: %s\n' % a.username)
        ui.write('password: %s\n' % a.password)
    else:
        ui.write('no auth\n')

@command('bzcreatecookie', [], 'hg bzcreatecookie [profiledir] [url] [userid] [cookie]')
def bzcreatecookie(ui, profiledir, url, userid, cookie):
    from mozhg.tests.test_auth import create_login_cookie

    create_login_cookie(profiledir, url, userid, cookie)
