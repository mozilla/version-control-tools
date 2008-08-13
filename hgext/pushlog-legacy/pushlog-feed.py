import mercurial.hgweb.protocol as hgwebprotocol
import mercurial.hgweb.webcommands as hgwebcommands
from mercurial.templatefilters import xmlescape
from mercurial.hgweb.common import HTTP_OK, HTTP_NOT_FOUND, HTTP_SERVER_ERROR, paritygen
from mercurial.node import short, bin, hex
from mercurial import demandimport

import sys, os.path, re
from datetime import datetime
import time
from math import ceil
import sys

sys.path.append(os.path.dirname(__file__))

demandimport.disable()
from parsedatetime import parsedatetime as pdt

try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite
demandimport.enable()

cal = pdt.Calendar()
PUSHES_PER_PAGE = 10

def addcommand(f, name):
    setattr(hgwebprotocol, name, f)
    hgwebprotocol.__all__.append(name)

def addwebcommand(f, name):
    setattr(hgwebcommands, name, f)
    hgwebcommands.__all__.append(name)

ATOM_MIMETYPE = 'application/atom+xml'

def getpushlogentries(conn, start, count, tipsonly):
    """Get entries from the push log. Select |count| pushes starting at offset
    |start|, in reverse chronological order, and then return all changes
    pushed in these pushes. Returns a list of tuples of
    (pushid, user, date, node). If |tipsonly| is True, return only the tip
    changeset from each push."""
    entries = []
    res = conn.execute("SELECT id, user, date FROM pushlog ORDER BY date DESC LIMIT ? OFFSET ?", (count,start))
    for (id,user,date) in res:
        limit = ""
        if tipsonly:
            limit = " LIMIT 1"
        res2 = conn.execute("SELECT node FROM changesets WHERE pushid = ? ORDER BY rev DESC" + limit, (id,))
        for node, in res2:
            entries.append((id,user,date,node))
    return entries

def getpushlogentriesbydate(conn, startdate, enddate, tipsonly):
    """Get entries in the push log in a date range. If |tipsonly| is True,
    return only the tip changeset from each push."""
    entries = []
    res = conn.execute("SELECT id, user, date, node FROM pushlog LEFT JOIN changesets ON id = pushid WHERE date > ? AND date < ? ORDER BY date DESC, rev DESC", (startdate, enddate))
    lastid = None
    for (id, user, date, node) in res:
        if tipsonly and id == lastid:
            continue
        entries.append((id,user,date,node))
        lastid = id
    return entries

def getpushlogentriesbychangeset(conn, fromchange, tochange, tipsonly):
    """Get entries in the push log between two changesets. Return changesets
    pushed after |fromchange|, up to and including |tochange|.
    If |tipsonly| is True, return only the tip changeset from each push."""
    entries = []
    # find the changeset before the first changeset
    fromchange += "%"
    e = conn.execute("SELECT pushid FROM changesets WHERE node LIKE ?", (fromchange,)).fetchone()
    if e is None:
        return []
    fromid = e[0]
    # find the last changeset
    tochange += "%"
    e = conn.execute("SELECT pushid FROM changesets WHERE node LIKE ?", (tochange,)).fetchone()
    if e is None:
        return []
    toid = e[0]
    if fromid >= toid:
        return []
    # now get all the changesets from right after fromchange, up to and
    # including tochange
    res = conn.execute("SELECT id, user, date, node FROM pushlog LEFT JOIN changesets ON id = pushid WHERE id > ? AND id <= ? ORDER BY date DESC, rev DESC", (fromid, toid))
    lastid = None
    for (id, user, date, node) in res:
        if tipsonly and id == lastid:
            continue
        entries.append((id,user,date,node))
        lastid = id
    return entries

def gettotalpushlogentries(conn):
    """Return the total number of pushes logged in the pushlog."""
    return conn.execute("SELECT COUNT(*) FROM pushlog").fetchone()[0]

def localdate(ts):
    t = time.localtime(ts)
    offset = time.timezone
    if t[8] == 1:
        offset = time.altzone
    return (ts, offset)

def doParseDate(datestring):
    try:
        date = time.strptime(datestring, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        date, x = cal.parse(datestring)
    return time.mktime(date)

def pushlogSetup(web, req):
    repopath = os.path.dirname(web.repo.path)
    reponame = os.path.basename(repopath)
    if reponame == '.hg':
        reponame = os.path.basename(os.path.dirname(repopath))
    pushdb = os.path.join(web.repo.path, "pushlog2.db")
    conn = sqlite.connect(pushdb)

    if 'node' in req.form:
        page = int(req.form['node'][0])
    else:
        page = 1

    tipsonly = False
    if 'tipsonly' in req.form and req.form['tipsonly'][0] == '1':
        tipsonly = True
    dates = []
    if 'startdate' in req.form and 'enddate' in req.form:
        startdate = doParseDate(req.form['startdate'][0])
        enddate = doParseDate(req.form['enddate'][0])
        dates = [{'startdate':localdate(startdate), 'enddate':localdate(enddate)}]
        page = 1
        total = 1
        e = getpushlogentriesbydate(conn, startdate, enddate, tipsonly)
    elif 'fromchange' in req.form and 'tochange' in req.form:
        fromchange = req.form['fromchange'][0]
        tochange = req.form['tochange'][0]
        page = 1
        total = 1
        e = getpushlogentriesbychangeset(conn, fromchange, tochange, tipsonly)
    else:
        e = getpushlogentries(conn, (page - 1) * PUSHES_PER_PAGE, 10, tipsonly)
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
    return (e, urlbase, reponame, total, page, dates)
    
def pushlogFeed(web, req):
    (e, urlbase, reponame, total, page, dates) = pushlogSetup(web, req)
    isotime = lambda x: datetime.utcfromtimestamp(x).isoformat() + 'Z'

    resp = ["""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <id>%(urlbase)s%(url)spushlog</id>
 <link rel="self" href="%(urlbase)s%(url)spushlog" />
 <updated>%(date)s</updated>
 <title>%(reponame)s Pushlog</title>""" % {'urlbase': urlbase,
                              'url': req.url,
                              'reponame': reponame,
                              'date': isotime(e[0][2])}];

    for id, user, date, node in e:
        ctx = web.repo.changectx(node)
        resp.append("""
 <entry>
  <title>Changeset %(node)s</title>
  <id>http://www.selenic.com/mercurial/#changeset-%(node)s</id>
  <link href="%(urlbase)s%(url)srev/%(node)s" />
  <updated>%(date)s</updated>
  <author>
   <name>%(user)s</name>
  </author>
  <content type="xhtml">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">%(files)s</li></ul>
    </div>
  </content>
 </entry>""" % {'node': node,
                'date': isotime(date),
                'user': xmlescape(user),
                'urlbase': urlbase,
                'url': req.url,
                'files': '</li><li class="file">'.join(ctx.files())})

    resp.append("</feed>")

    resp = "".join(resp)

    req.respond(HTTP_OK, ATOM_MIMETYPE, length=len(resp))
    req.write(resp)

def pushlogHTML(web, req, tmpl):
    (entries, urlbase, reponame, total, page, dates) = pushlogSetup(web, req)

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
        start = max(1, page - PUSHES_PER_PAGE/2)
        end = min(numpages + 1, page + PUSHES_PER_PAGE/2)
        if page != 1:
            nav.append({'page': 1, 'label': "First"})
            nav.append({'page': page - 1, 'label': "Prev"})
        for i in range(start, end):
            nav.append({'page': i, 'label': str(i)})
        
        if page != numpages:
            nav.append({'page': page + 1, 'label': "Next"})
            nav.append({'page': numpages, 'label': "Last"})
        return nav

    def changelist(limit=0, **map):
        allentries = []
        lastid = None
        ch = None
        l = []
        for id, user, date, node in entries:
            if id != lastid:
                lastid = id
                l.append({"parity": parity.next(),
                          "user": user,
                          "date": localdate(date),
                          'numchanges': 0,
                          "changes": []})
                ch = l[-1]['changes']
            ctx = web.repo.changectx(node)
            n = ctx.node()
            ch.append({"author": ctx.user(),
                       "desc": ctx.description(),
                       "files": web.listfilediffs(tmpl, ctx.files(), n),
                       "rev": ctx.rev(),
                       "node": hex(n),
                       "tags": nodetagsdict(web.repo, n),
                       "branches": nodebranchdict(web.repo, ctx),
                       "inbranch": nodeinbranch(web.repo, ctx),
                       "parity": l[-1]["parity"]
                       })
            l[-1]['numchanges'] += 1

        if limit > 0:
            l = l[:limit]

        for e in l:
            yield e

    parity = paritygen(web.stripecount)

    if 'startdate' in req.form and 'enddate' in req.form:
        startdate = req.form['startdate']
        enddate = req.form['enddate']
    else:
        startdate = "1 week ago"
        enddate = "now"
    return tmpl('pushlog',
                changenav=changenav(),
                rev=0,
                entries=lambda **x: changelist(limit=0,**x),
                latestentry=lambda **x: changelist(limit=1,**x),
                startdate=startdate,
                enddate=enddate,
                query=dates,
                archives=web.archivelist("tip"))


addcommand(pushlogFeed, 'pushlog')
addwebcommand(pushlogHTML, 'pushloghtml')

cmdtable = {}
