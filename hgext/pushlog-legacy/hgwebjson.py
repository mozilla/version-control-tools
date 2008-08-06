from mercurial import demandimport, context, util
from mercurial.node import hex, nullid
import mercurial.hgweb.protocol as hgwebprotocol
from mercurial.hgweb.common import HTTP_OK, HTTP_NOT_FOUND, HTTP_SERVER_ERROR
from mercurial.hgweb.hgwebdir_mod import hgwebdir

demandimport.disable()
import simplejson
demandimport.enable()

isodate = lambda x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')

class HGJSONEncoder(simplejson.JSONEncoder):
    def __init__(self):
        simplejson.JSONEncoder.__init__(self, indent=1)

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

def printjson(ui, repo, *args):
    e = HGJSONEncoder(repo)
    print e.encode([repo.changectx(arg) for arg in args])

# For kicks and testing, add a command-line JSON printer

cmdtable = {
    'printjson': (printjson, [], "hg printjson [rev...]"),
}

# Add hgweb hooks

def addwebcommand(f, name):
    setattr(hgwebprotocol, name, f)
    hgwebprotocol.__all__.append(name)

JSON_MIMETYPE = 'application/json'

def heads(web, req):
    e = HGJSONEncoder()
    resp = e.encode([web.repo.changectx(n) for n in web.repo.heads()])
    req.respond(HTTP_OK, JSON_MIMETYPE, length=len(resp))
    req.write(resp)

addwebcommand(heads, 'jsonheads')

def tags(web, req):
    tags = web.repo.tagslist()
    e = HGJSONEncoder()
    resp = e.encode([{'tag': tag,
                      'changeset': web.repo.changectx(node)}
                     for tag, node in tags])
    req.respond(HTTP_OK, JSON_MIMETYPE, length=len(resp))
    req.write(resp)

addwebcommand(tags, 'jsontags')

def family(web, req):
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

    e = HGJSONEncoder(web.repo)
    resp = e.encode({'context': hex(ctx.node()),
                     'nodes': nodelist})
    req.respond(HTTP_OK, JSON_MIMETYPE, length=len(resp))
    req.write(resp)

addwebcommand(family, 'jsonfamily')    

def info(web, req):
    """Get JSON information about the specified nodes."""
    e = HGJSONEncoder()
    d = {}
    for node in req.form['node']:
        d[node] = web.repo.changectx(node)

    resp = e.encode(d)
    req.respond(HTTP_OK, JSON_MIMETYPE, length=len(resp))
    req.write(resp)

addwebcommand(info, 'jsoninfo')
