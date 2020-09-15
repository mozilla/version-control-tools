# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

'''Ability to mark repositories as read only.

This extension looks for up to 2 files signaling that the repository should be
read-only. First, it looks in ``.hg/readonlyreason``. If the file is present,
the repository is read only. If the file has content, the content will be
printed to the user informing them of the reason the repo is read-only.

If the ``readonly.globalreasonfile`` config option is set, it defines another
path to be checked. It operates the same as ``.hg/readonlyreason`` except it
can be set in your global hgrc to allow a single file to mark all repositories
as read only.
'''

import errno

from mercurial.i18n import _
from mercurial import (
    registrar,
    util,
)

testedwith = b'4.3 4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1 5.2 5.3 5.4 5.5'
minimumhgversion = b'4.3'
buglink = b'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org'


configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'readonly', b'globalreasonfile',
           default=None)


def prechangegrouphook(ui, repo, **kwargs):
    return checkreadonly(ui, repo, b'add changesets')


def prepushkeyhook(ui, repo, namespace=None, **kwargs):
    return checkreadonly(ui, repo, b'update %s' % namespace)


def checkreadonly(ui, repo, op):
    try:
        reporeason = repo.vfs.read(b'readonlyreason')

        ui.warn(_(b'repository is read only\n'))
        if reporeason:
            ui.warn(reporeason.strip() + b'\n')

        ui.warn(_(b'refusing to %s\n') % op)
        return True
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise

    # Repo local file does not exist. Check global file.
    rf = ui.config(b'readonly', b'globalreasonfile')
    if rf:
        try:
            with util.posixfile(rf, b'rb') as fh:
                globalreason = fh.read()

            ui.warn(_(b'all repositories currently read only\n'))
            if globalreason:
                ui.warn(globalreason.strip() + b'\n')

            ui.warn(_(b'refusing to %s\n') % op)
            return True
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    return False


def reposetup(ui, repo):
    # HG 3.6 COMPAT
    # Ideally we'd use pretxnopen. However
    # https://bz.mercurial-scm.org/show_bug.cgi?id=4939 means hook output won't
    # be displayed. So we do it the old fashioned way.
    ui.setconfig(b'hooks', b'prechangegroup.readonly', prechangegrouphook, b'readonly')
    ui.setconfig(b'hooks', b'prepushkey.readonly', prepushkeyhook, b'readonly')
