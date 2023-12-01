# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension for vcsreplicator consumers."""

from __future__ import absolute_import

from mercurial import (
    bookmarks as bookmod,
    extensions,
)

testedwith = b"4.3 4.4 4.5 4.6 4.7 4.8 4.9 5.0 5.1 5.2 5.3 5.4 5.5"
minimumhgversion = b"4.3"


def bookmarks_updatefromremote(orig, ui, repo, remotemarks, *args, **kwargs):
    """Wraps bookmarks.updatefromremote() to force use remote values.

    We change the arguments to make it appear that all remote bookmarks were
    explicitly requested. That simulates a force pull and allows divergence
    without the poor naming.
    """
    # By default, the remote bookmarks are compared to the local bookmarks
    # and actions are taken. The action for diverged bookmarks is to create a
    # new local bookmark of the name ``foo@N``. This obviously isn't wanted
    # on a mirror.
    #
    # There are various ways we could trick the original function to do what we
    # want. Our solution is to just remove all local bookmarks. Mercurial
    # fetches the full set of bookmarks during pull operations. So this
    # effectively simulates all incoming bookmarks as being new/canonical.
    local_bookmarks = repo._bookmarks
    for book in list(local_bookmarks):
        local_bookmarks._del(book)

    return orig(ui, repo, remotemarks, *args, **kwargs)


def extsetup(ui):
    extensions.wrapfunction(bookmod, "updatefromremote", bookmarks_updatefromremote)
