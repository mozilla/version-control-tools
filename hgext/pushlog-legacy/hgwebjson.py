from mercurial.hgweb import webcommands


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
