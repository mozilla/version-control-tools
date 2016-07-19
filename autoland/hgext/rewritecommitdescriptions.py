# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
import json
import os

from mercurial import (context,
                       cmdutil,
                       encoding,
                       error,
                       extensions,
                       phases)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', '..', 'hgext', 'bootstrap.py'))

from mozhg import rewrite

testedwith = '3.5'

cmdtable = {}
command = cmdutil.command(cmdtable)


@command('rewritecommitdescriptions',
         [('', 'descriptions', '',
           'path to json file with new commit descriptions', 'string')],
         'hg rewritecommitdescriptions')
def rewrite_commit_descriptions(ui, repo, base_node, descriptions=None):

    def sha1_of(node):
        return repo[node].hex()[:12]

    # Rewriting fails if the evolve extension is enabled.
    try:
        extensions.find('evolve')
        raise error.Abort('Cannot continue as the "evolve" extension is '
                          'enabled.')
    except KeyError:
        pass

    # Read commit descriptions map.
    description_map = {}
    with open(descriptions, 'rb') as f:
        raw_descriptions = json.load(f)
        for sha1 in raw_descriptions:
            description_map[sha1[:12]] = encoding.tolocal(
                raw_descriptions[sha1].encode('utf-8'))

    # Collect nodes listed by description_map.
    nodes = []

    def add_node(ctx):
        node = ctx.node()
        if sha1_of(node) in description_map:
            nodes.append(node)

    ctx = repo[base_node]
    add_node(ctx)
    for ancestor in ctx.ancestors():
        if ctx.phase() != phases.draft:
            break
        add_node(repo[ancestor])
    nodes.reverse()

    if not nodes:
        raise error.Abort('No commits found to be rewritten.')

    # We need to store the original sha1 values because we won't be able to
    # look them up once they are rewritten.
    original_sha1s = {}
    for node in nodes:
        original_sha1s[node] = sha1_of(node)

    # Update changed nodes.
    def prune_unchanged(node):
        return repo[node].description() != description_map[sha1_of(node)]

    def create_func(repo, ctx, revmap, filectxfn):
        parents = rewrite.newparents(repo, ctx, revmap)

        sha1 = ctx.hex()[:12]
        description = description_map[sha1]

        memctx = context.memctx(repo, parents, description,
                                ctx.files(), filectxfn, user=ctx.user(),
                                date=ctx.date(), extra=ctx.extra())
        status = ctx.p1().status(ctx)
        memctx.modified = lambda: status[0]
        memctx.added = lambda: status[1]
        memctx.removed = lambda: status[2]

        return memctx

    node_map = {}
    changed_nodes = filter(prune_unchanged, nodes)
    if changed_nodes:
        node_map = rewrite.replacechangesets(repo, changed_nodes, create_func)

    # Output result.
    for node in nodes:
        original_sha1 = original_sha1s[node]
        if node in node_map:
            new_sha1 = sha1_of(node_map[node])
        else:
            new_sha1 = original_sha1s[node]
        ui.write('rev: %s -> %s\n' % (original_sha1, new_sha1))
