# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
import json
import os
import sys

from mercurial import (context,
                       cmdutil,
                       encoding,
                       phases)

from mercurial.i18n import _

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', '..', 'hgext', 'bootstrap.py'))

from mozhg import rewrite

testedwith = '3.5'

cmdtable = {}
command = cmdutil.command(cmdtable)


@command('rewritecommitdescriptions',
         [('', 'descriptions', '',
           'path to json file with new commit descriptions', 'string')],
         _('hg rewritecommitdescriptions'))
def rewrite_commit_descriptions(ui, repo, node, descriptions=None):

    description_map = {}
    with open(descriptions, 'rb') as f:
        raw_descriptions = json.load(f)
        for k in raw_descriptions:
            description_map[k[:12]] = encoding.tolocal(raw_descriptions[k].encode('utf-8'))

    if not node:
        node = 'tip'

    ctx = repo[node]
    nodes = [ctx.node()]
    for ancestor in ctx.ancestors():
        ctx = repo[ancestor]
        if ctx.phase() != phases.draft:
            break
        sha1 = repo[ctx.node()].hex()[:12]
        if sha1 in description_map:
            nodes.append(ctx.node())
    nodes.reverse()

    if not nodes:
        ui.write(_('no commits found to be rewritten\n'))
        return 1

    oldest_relevant_commit = repo[nodes[0]].hex()[:12]

    def prune_unchanged(node):
        sha1 = repo[node].hex()[:12]
        description = repo[node].description()
        revised_description = description_map.get(sha1, description)
        if description == revised_description:
            ui.write(_('not rewriting %s - description unchanged\n' % sha1))
            return False
        return True

    nodes = filter(prune_unchanged, nodes)
    if not nodes:
        ui.write(_('no commits found to be rewritten\n'))
        # in this case, we need to output the sha1 of the oldest commit
        # present in commit descriptions
        ui.write('base: ' + oldest_relevant_commit + '\n')
        return 0

    def createfn(repo, ctx, revmap, filectxfn):
        parents = rewrite.newparents(repo, ctx, revmap)

        sha1 = ctx.hex()[:12]
        if sha1 in description_map:
            description = description_map[sha1]
        else:
            description = ctx.description()

        memctx = context.memctx(repo, parents, description,
                                ctx.files(), filectxfn, user=ctx.user(),
                                date=ctx.date(), extra=ctx.extra())
        status = ctx.p1().status(ctx)
        memctx.modified = lambda: status[0]
        memctx.added = lambda: status[1]
        memctx.removed = lambda: status[2]

        return memctx

    # we output the sha1 of the oldest modified commit
    nodemap = rewrite.replacechangesets(repo, nodes, createfn)
    ui.write('base: ' + repo[nodemap[nodes[0]]].hex()[:12] + '\n')
    return 0
