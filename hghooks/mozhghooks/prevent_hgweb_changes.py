# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

# This hook is intended to run on the hgweb machines. It effectively
# prevents repository changes that didn't come from `hg pull` or
# `hg strip`. The former is used by the replication mechanism. The
# latter is an adminstrative task that is performed from time to time.
#
# Ideally we would also prevent transaction opens and the use of the
# pushkey protocol. However, the replication mechanism uses `hg debugpushkey`
# and pushkey hooks don't get enough information to know the source of the
# change. And the set of transaction names is too large to screen. So this
# is the best we can do for now.


def precommit(ui, repo, *args, **kwargs):
    ui.write(b"illegal change to repository!\n")
    ui.write(
        b"local commits are not allowed on HTTP replicas; "
        b"all repository changes must be made via replication mechanism\n"
    )
    return 1


def pretxnchangegroup(ui, repo, node, source=None, **kwargs):
    # Allow changes that come from replication mechanism or as the result of
    # a strip operation.
    if source in (b"pull", b"strip"):
        return 0

    # All other changes should be denied.
    ui.write(b"illegal change to repository\n")
    ui.write(
        b"changes to repositories on HTTP replicas can only be made "
        b"through the replication system; a change via %s is not "
        b"allowed\n" % source
    )
    return 1
