# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.
import json
import os

from mercurial import (
    context,
    cmdutil,
    encoding,
    error,
    extensions,
    phases,
    registrar,
    util,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', '..', 'hgext', 'bootstrap.py'))

from mozhg import rewrite

minimumhgversion = '4.1'
testedwith = '4.1 4.2'

cmdtable = {}

# Mercurial 4.3 introduced registrar.command as a replacement for
# cmdutil.command.
if util.safehasattr(registrar, 'command'):
    command = registrar.command(cmdtable)
else:
    command = cmdutil.command(cmdtable)


@command('rewritecommitdescriptions',
         [('', 'descriptions', '',
           'path to json file with new commit descriptions', 'string')],
         'hg rewritecommitdescriptions')
def rewrite_commit_descriptions(ui, repo, base_node, descriptions=None):

    def sha1_short(node):
        return repo[node].hex()[:12]

    def sha1_full(node):
        return repo[node].hex()

    # Rewriting fails if the evolve extension is enabled.
    try:
        extensions.find('evolve')
        raise error.Abort('Cannot continue as the "evolve" extension is '
                          'enabled.')
    except KeyError:
        pass

    # Read commit descriptions map.
    # MozReview passes in short SHA1 (12 chars), so we have to use [:12] here
    # and in `add_node`.
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
        if sha1_short(node) in description_map:
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
        original_sha1s[node] = sha1_full(node)

    # Update changed nodes.
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

    node_map = rewrite.replacechangesets(repo, nodes, create_func)

    # Output result.
    for node in nodes:
        ui.write('rev: %s -> %s\n' % (original_sha1s[node],
                                      sha1_full(node_map[node])))
