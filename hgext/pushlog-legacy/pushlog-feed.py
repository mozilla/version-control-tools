import mercurial.hgweb.webcommands as hgwebcommands
from mercurial.templatefilters import xmlescape
from mercurial.hgweb.common import HTTP_OK, HTTP_NOT_FOUND, HTTP_SERVER_ERROR, paritygen
from mercurial.node import short, bin, hex
from mercurial import demandimport

import sys, os.path, re
from datetime import datetime
from math import ceil
import sys

demandimport.disable()
try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite
demandimport.enable()

PUSHES_PER_PAGE = 10

def addwebcommand(f, name):
    setattr(hgwebcommands, name, f)
    hgwebcommands.__all__.append(name)

ATOM_MIMETYPE = 'application/atom+xml'

def getpushlogentries(conn, start, count):
    """Get entries from the push log. Select |count| pushes starting at offset
    |start|, in reverse chronological order, and then return all changes
    pushed in these pushes. Returns a list of tuples of
    (pushid, user, date, node)."""
    entries = []
    res = conn.execute("SELECT id, user, date FROM pushlog ORDER BY date DESC LIMIT ? OFFSET ?", (count,start))
    for (id,user,date) in res:
        res2 = conn.execute("SELECT node FROM changesets WHERE pushid = ? ORDER BY rev DESC", (id,))
        for node, in res2:
            entries.append((id,user,date,node))
    return entries

def gettotalpushlogentries(conn):
    """Return the total number of pushes logged in the pushlog."""
    return conn.execute("SELECT COUNT(*) FROM pushlog").fetchone()[0]

def pushlogSetup(web, req):
    repopath = os.path.dirname(web.repo.path)
    reponame = os.path.basename(repopath)
    if reponame == '.hg':
        reponame = os.path.basename(os.path.dirname(repopath))
    pushdb = os.path.join(web.repo.path, "pushlog2.db")
    conn = sqlite.connect(pushdb)

    if 'node' in req.form:
        start = int(req.form['node'][0])
    else:
        start = 0
    e = getpushlogentries(conn, start * PUSHES_PER_PAGE, 10)
    total = gettotalpushlogentries(conn)
    proto = req.env.get('wsgi.url_scheme')
    if proto == 'https':
        proto = 'https'
        default_port = "443"
    else:
        proto = 'http'
        default_port = "80"
    port = req.env["SERVER_PORT"]
    port = port != default_port and (":" + port) or ""

    urlbase = '%s://%s%s' % (proto, req.env['SERVER_NAME'], port)
    return (e, urlbase, reponame, total, start)
    
def pushlogFeed(web, req, tmpl):
    (e, urlbase, reponame, total, page) = pushlogSetup(web, req)

    resp = ["""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <id>%(urlbase)s%(url)spushlog</id>
 <link rel="self" href="%(urlbase)s%(url)spushlog" />
 <updated>%(date)s</updated>
 <title>%(reponame)s Pushlog</title>""" % {'urlbase': urlbase,
                              'url': req.url,
                              'reponame': reponame,
                              'date': e[0][2]}];

    for id, user, date, node in e:
        resp.append("""
 <entry>
  <title>Changeset %(node)s</title>
  <id>http://www.selenic.com/mercurial/#changeset-%(node)s</id>
  <link href="%(urlbase)s%(url)srev/%(node)s" />
  <updated>%(date)s</updated>
  <author>
   <name>%(user)s</name>
  </author>
 </entry>""" % {'node': node,
                'date': datetime.utcfromtimestamp(date).isoformat()+"Z",
                'user': xmlescape(user),
                'urlbase': urlbase,
                'url': req.url})

    resp.append("</feed>")

    resp = "".join(resp)

    req.respond(HTTP_OK, ATOM_MIMETYPE, length=len(resp))
    req.write(resp)

def pushlogHTML(web, req, tmpl):
    (entries, urlbase, reponame, total, page) = pushlogSetup(web, req)

    # these three functions are in webutil in newer hg, but not in hg 1.0
    def nodetagsdict(repo, node):
        return [{"name": i} for i in repo.nodetags(node)]

    def nodebranchdict(repo, ctx):
        branches = []
        branch = ctx.branch()
        # If this is an empty repo, ctx.node() == nullid,
        # ctx.branch() == 'default', but branchtags() is
        # an empty dict. Using dict.get avoids a traceback.
        if repo.branchtags().get(branch) == ctx.node():
            branches.append({"name": branch})
        return branches

    def nodeinbranch(repo, ctx):
        branches = []
        branch = ctx.branch()
        if branch != 'default' and repo.branchtags().get(branch) != ctx.node():
            branches.append({"name": branch})
        return branches

    def changenav():
        nav = []
        numpages = int(ceil(total / float(PUSHES_PER_PAGE)))
        start = max(0, page - PUSHES_PER_PAGE/2)
        end = min(numpages, page + PUSHES_PER_PAGE/2)
        if page != 0:
            nav.append({'page': 0, 'label': "First"})
            nav.append({'page': page - 1, 'label': "Prev"})
        for i in range(start, end):
            nav.append({'page': i, 'label': str(i+1)})
        
        if page != numpages - 1:
            nav.append({'page': page + 1, 'label': "Next"})
            nav.append({'page': numpages - 1, 'label': "Last"})
        return nav
    
    def changelist(limit=0, **map):
        allentries = []
        lastid = None
        lastparity = 0
        l = []
        for id, user, date, node in entries:
            ctx = web.repo.changectx(node)
            if id == lastid:
                p = lastparity
            else:
                p = parity.next()
                lastparity = p
                lastid = id
            n = ctx.node()
            l.append({"parity": p,
                      "author": user,
                      "desc": ctx.description(),
                      "date": (date, 0),
                      "files": web.listfilediffs(tmpl, ctx.files(), n),
                      "rev": ctx.rev(),
                      "node": hex(n),
                      "tags": nodetagsdict(web.repo, n),
                      "branches": nodebranchdict(web.repo, ctx),
                      "inbranch": nodeinbranch(web.repo, ctx)
                      })


        if limit > 0:
            l = l[:limit]

        for e in l:
            yield e

    parity = paritygen(web.stripecount)

    return tmpl('pushlog',
                changenav=changenav(),
                rev=0,
                entries=lambda **x: changelist(limit=0,**x),
                latestentry=lambda **x: changelist(limit=1,**x),
                archives=web.archivelist("tip"))


addwebcommand(pushlogFeed, 'pushlog')
addwebcommand(pushlogHTML, 'pushloghtml')

cmdtable = {}
