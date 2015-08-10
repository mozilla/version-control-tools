from mercurial import demandimport, context, util
from mercurial.node import hex, nullid
from mercurial.hgweb import webcommands
from mercurial import templatefilters

demandimport.disable()
import json
demandimport.enable()

isodate = lambda x: util.datestr(x, '%Y-%m-%d %H:%M %1%2')

class HGJSONEncoder(json.JSONEncoder):
    def __init__(self):
        json.JSONEncoder.__init__(self, indent=1, sort_keys=True)

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

        return json.JSONEncoder.default(self, v)

templatefilters.filters['mozjson'] = HGJSONEncoder()

# Add hgweb hooks

def addwebcommand(f, name):
    setattr(webcommands, name, f)
    webcommands.__all__.append(name)


def info(web, req, tmpl):
    """Get JSON information about the specified nodes."""
    if 'node' not in req.form:
        return tmpl('error', error={'error': "missing parameter 'node'"})
    nodes = dict((n, web.repo.changectx(n)) for n in req.form['node'])
    return tmpl('info', nodes=nodes)

addwebcommand(info, 'info')
