# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Dummy extension to force hgwebdir to always refresh.

By default, hgwebdir only refreshes every 20 seconds. This means that if
we create a new repository, it doesn't appear on hgweb for 20 seconds.

We have tests that use hgwebdir and we need hgweb to respond to new
repositories without waiting 20 seconds or requiring a process restart.

Installing this extension forces hgwebdir to refresh on every request.
This does result in a slight performance loss. But this extension should
only be used as part of tests, so it shouldn't matter.
"""


from mercurial.extensions import wrapfunction
import mercurial.hgweb as hgweb

def wrappedhgweb(orig, *args, **kwargs):
    web = orig(*args, **kwargs)

    if isinstance(web, hgweb.hgwebdir_mod.hgwebdir):
        web.refreshinterval = -1

    return web


def extsetup(ui):
    wrapfunction(hgweb, 'hgweb', wrappedhgweb)
