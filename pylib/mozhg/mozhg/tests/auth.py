# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Dummy Mercurial extension to facilitate testing of mozhg.auth.getbugzillaauth()."""

import getpass
import os

from mercurial import (
    cmdutil,
    pycompat,
    registrar,
    util,
)

OUR_DIR = os.path.dirname(__file__)
with open(os.path.join(OUR_DIR, "..", "..", "..", "..", "hgext", "bootstrap.py")) as f:
    exec(f.read())

from mozhg.auth import (
    getbugzillaauth,
    register_config_items,
)

cmdtable = {}
command = registrar.command(cmdtable)

configtable = {}
configitem = registrar.configitem(configtable)

register_config_items(configitem)


@command(
    b"bzauth",
    [
        (b"", b"require", False, b"Require auth"),
        (b"", b"fakegetpass", b"", b"Provide a fake getpass.getpass answer"),
        (b"", b"ffprofile", b"", b"Firefox profile to use"),
    ],
    b"hg bzauth",
    norepo=True,
)
def bzauth(ui, require=False, fakegetpass=None, ffprofile=None):
    if fakegetpass:

        def newgetpass(arg):
            return fakegetpass

        getpass.getpass = newgetpass

    a = getbugzillaauth(ui, require=require, profile=ffprofile)
    if a:
        ui.write(b"userid: %s\n" % pycompat.bytestr(a.userid))
        ui.write(b"cookie: %s\n" % pycompat.bytestr(a.cookie))
        ui.write(b"username: %s\n" % pycompat.bytestr(a.username))
        ui.write(b"password: %s\n" % pycompat.bytestr(a.password))
        ui.write(b"apikey: %s\n" % pycompat.bytestr(a.apikey))
    else:
        ui.write(b"no auth\n")


@command(
    b"bzcreatecookie",
    [],
    b"hg bzcreatecookie [profiledir] [url] [userid] [cookie]",
    norepo=True,
)
def bzcreatecookie(ui, profiledir, url, userid, cookie):
    from mozhg.tests.test_auth import create_login_cookie

    create_login_cookie(profiledir, url, userid, cookie)
