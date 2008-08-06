from mercurial import demandimport, context, util
from mercurial.node import hex, nullid
from mercurial.hgweb import webcommands
from mercurial import templatefilters

demandimport.disable()
import simplejson
demandimport.enable()

isodate = lambda x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')

class HGJSONEncoder(simplejson.JSONEncoder):
    def __init__(self):
        simplejson.JSONEncoder.__init__(self, indent=1)

    def __call__(self, obj):
        return self.encode(obj)

    def default(self, v):
        if isinstance(v, context.changectx):
            return {'rev':         v.rev(),
                    'node':        hex(v.node()),
                    'user':        v.user(),
                    'date':        isodate(v.date()),
                    'description': v.description(),
                    'branch':      v.branch(),
                    'tags':        v.tags(),
                    'parents':     [hex(n.node()) for n in v.parents()
                                    if n != nullid],
                    'children':    [hex(n.node()) for n in v.children()
                                    if n != nullid],
                    'files':       v.files(),
                    }
        
        if isinstance(v, context.filectx):
            return {'filerev':     v.filerev(),
                    'filenode':    hex(v.filenode())}

        if hasattr(v, '__iter__'):
            return [o for o in v]

        return simplejson.JSONEncoder.default(self, v)

templatefilters.filters['mozjson'] = HGJSONEncoder()

def printjson(ui, repo, *args):
    e = HGJSONEncoder(repo)
    print e.encode([repo.changectx(arg) for arg in args])

# For kicks and testing, add a command-line JSON printer

cmdtable = {
    'printjson': (printjson, [], "hg printjson [rev...]"),
}

# Add hgweb hooks

def addwebcommand(f, name):
    setattr(webcommands, name, f)
    webcommands.__all__.append(name)

def heads(web, req, tmpl):
    heads = web.repo.heads()
    return tmpl('heads', heads=[web.repo.changectx(n) for n in heads])

addwebcommand(heads, 'webheads')

def tags(web, req, tmpl):
    return tmpl('tags', tags=[{'tag': tag,
                               'changeset': web.repo.changectx(node)}
                              for tag, node in web.repo.tagslist()])

addwebcommand(tags, 'webtags')

def family(web, req, tmpl):
    """Get all the changesets related to a particular node, both children and
    parents, by walking backwards/forwards to a limit."""

    node = req.form['node'][0]
    ctx = web.repo.changectx(node)

    try:
        limit = int(req.form['limit'][0])
    except KeyError:
        limit = 2

    nodelist = [ctx]

    def children(n, curlimit):
        for p in n.children():
            nodelist.append(p)
            if curlimit < limit:
                children(p, curlimit + 1)

    def parents(n, curlimit):
        for p in n.parents():
            if p:
                nodelist.append(p)
            if curlimit < limit:
                parents(p, curlimit + 1)

    children(ctx, 1)
    parents(ctx, 1)
    return tmpl('family', family={'context': hex(ctx.node()),
                                  'nodes': nodelist})

addwebcommand(family, 'family')

def info(web, req, tmpl):
    """Get JSON information about the specified nodes."""
    nodes = dict((n, web.repo.changectx(n)) for n in req.form['node'])
    return tmpl('info', nodes=nodes)

addwebcommand(info, 'info')
