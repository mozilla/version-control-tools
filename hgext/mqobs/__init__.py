# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Write obsolescence markers with mq.

This extension enhances mq commands to produce obsolescence markers.

Currently, we only write markers during the qrefresh command. The
following do *not* result in marker creation:

* qpush (apply on top of a different parent)
* qdelete
* qfold

It is difficult to write obsolescence markers during these operations
because mq doesn't always track the node associated with the patch.
To write an obsolescence marker, we need to know the before and after
after. To capture these before nodes, we'd need to perform an exact
apply before the operation, capture the old node, unapply, then apply
to the new parent. This can fail and is somewhat complicated to do
right. Maybe in a later version.
"""

from mercurial import extensions
from mercurial import hg
from mercurial import localrepo
from mercurial import obsolete
from mercurial import util
from mercurial.i18n import _
from hgext import mq

from StringIO import StringIO

testedwith = '3.0.1'

obsolete._enabled = True

def createmarker(repo, oldnode, newctx, flag=0):
    """Reimplement obsolete.createmarkers to accept a node that doesn't exist.

    We can't use obsolete.createmarkers with mq because the original
    implementation assumes the old changeset is present in the
    repository. This function reimplements the basic functionality
    taking nodes instead of changectx as arguments.
    """
    assert len(oldnode) == 20

    if oldnode == newctx.node():
        raise util.Abort('cannot obsolete self')

    metadata = {'date': newctx.date(), 'user': newctx.user()}
    tr = repo.transaction('add-obsolescence-marker')
    try:
        repo.obsstore.create(tr, oldnode, (newctx.node(),), flag, metadata)
        repo.filteredrevcache.clear()
        tr.close()
    finally:
        tr.release()

def qrefresh(orig, ui, repo, *args, **kwargs):
    q = repo.mq

    if not q.applied:
        return orig(ui, repo, *args, **kwargs)

    oldctx = repo[q.applied[-1].node]
    ret = orig(ui, repo, *args, **kwargs)
    newctx = repo[q.applied[-1].node]

    if oldctx.node() != newctx.node():
        createmarker(repo, oldctx.node(), newctx)

    return ret

def extsetup(ui):
    try:
        mq = extensions.find('mq')
    except KeyError:
        raise util.Abort(_('mqobs extension requires mq to be loaded.'))

    extensions.wrapcommand(mq.cmdtable, 'qrefresh', qrefresh)
