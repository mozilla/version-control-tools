# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os

from mercurial import (
    cmdutil,
    context,
)


OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', '..', '..', '..', 'hgext', 'bootstrap.py'))

from mozhg.rewrite import (
    newparents,
    replacechangesets,
)


cmdtable = {}
command = cmdutil.command(cmdtable)


@command('rewritemessage', [], 'hg rewrite REVS')
def rewritemessage(ui, repo, revs=None):
    nodes = [repo[rev].node() for rev in repo.revs(revs)]
    offset = [0]

    def createfn(repo, ctx, revmap, filectxfn):
        parents = newparents(repo, ctx, revmap)
        memctx = context.memctx(repo, parents,
                                ctx.description() + '\n%d' % offset[0],
                                ctx.files(), filectxfn, user=ctx.user(),
                                date=ctx.date(), extra=ctx.extra())
        status = ctx.p1().status(ctx)
        memctx.modified = lambda: status[0]
        memctx.added = lambda: status[1]
        memctx.removed = lambda: status[2]
        offset[0] += 1

        return memctx

    replacechangesets(repo, nodes, createfn)


@command('rewritechangefile', [], 'hg rewrite REVS')
def rewritechangefile(ui, repo, revs=None):
    nodes = [repo[rev].node() for rev in repo.revs(revs)]

    def createfn(repo, ctx, revmap, filectxfn):
        parents = newparents(repo, ctx, revmap)

        files = ctx.files()
        files.pop()
        memctx = context.memctx(repo, parents, ctx.description(),
                                files, filectxfn, user=ctx.user(),
                                date=ctx.date(), extra=ctx.extra())

        return memctx

    replacechangesets(repo, nodes, createfn)
