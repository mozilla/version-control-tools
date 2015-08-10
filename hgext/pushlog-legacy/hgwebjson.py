from mercurial import context, util
from mercurial.node import hex, nullid
from mercurial.hgweb import webcommands
from mercurial import templatefilters

import json

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

    csets = []
    for node in req.form['node']:
        ctx = web.repo[node]
        csets.append({
            'rev': ctx.rev(),
            'node': ctx.hex(),
            'user': ctx.user(),
            'date': ctx.date(),
            'description': ctx.description(),
            'branch': ctx.branch(),
            'tags': ctx.tags(),
            'parents': [p.hex() for p in ctx.parents()],
            'children': [c.hex() for c in ctx.children()],
            'files': ctx.files(),
        })

    return tmpl('info', csets=csets)


addwebcommand(info, 'info')
