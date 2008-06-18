import mercurial.hgweb.protocol as hgwebprotocol
from mercurial.templatefilters import xmlescape
from mercurial.hgweb.common import HTTP_OK, HTTP_NOT_FOUND, HTTP_SERVER_ERROR
from mercurial.node import short, bin
from mercurial import demandimport
import os.path
import re
import time

demandimport.disable()
try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite
demandimport.enable()

def addwebcommand(f, name):
    setattr(hgwebprotocol, name, f)
    hgwebprotocol.__all__.append(name)

ATOM_MIMETYPE = 'application/atom+xml'

def lastNEntries(pushdb, n):
    conn = sqlite.connect(pushdb)
    res = conn.execute("SELECT node, user, date FROM pushlog ORDER BY date DESC LIMIT ?", (n,))
    return res.fetchall()

def pushlogSetup(web, req):
    repopath = os.path.dirname(web.repo.path)
    reponame = os.path.basename(repopath)
    if reponame == '.hg':
        reponame = os.path.basename(os.path.dirname(repopath))
    pushdb = os.path.join(web.repo.path, "pushlog.db")
    e = lastNEntries(pushdb, 10)
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
    return (e, urlbase, reponame)
    
def pushlogFeed(web, req):
    (e, urlbase, reponame) = pushlogSetup(web, req)

    resp = ["""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <id>%(urlbase)s%(url)spushlog</id>
 <link rel="self" href="%(urlbase)s%(url)spushlog" />
 <updated>%(date)s</updated>
 <title>%(reponame)s Pushlog</title>""" % {'urlbase': urlbase,
                              'url': req.url,
                              'reponame': reponame,
                              'date': e[0][2]}];

    for node, user, date in e:
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
                'date': date,
                'user': xmlescape(user),
                'urlbase': urlbase,
                'url': req.url})

    resp.append("</feed>")

    resp = "".join(resp)

    req.respond(HTTP_OK, ATOM_MIMETYPE, length=len(resp))
    req.write(resp)

def pushlogHTML(web, req):
    (e, urlbase, reponame) = pushlogSetup(web, req)

    resp = ["""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US" lang="en-US">
<head>
<link rel="icon" href="%(urlbase)s/static/hgicon.png" type="image/png" />
<meta name="robots" content="index, nofollow"/>
<link rel="stylesheet" href="%(urlbase)s/static/style-gitweb.css" type="text/css" />
<title>%(reponame)s pushlog</title>
<link rel="alternate" type="application/atom+xml"
   href="%(urlbase)s/pushlog" title="Atom feed for %(reponame)s pushlog"/>
</head>
<body>
<div class="page_header">
<a href="http://developer.mozilla.org/en/docs/Mercurial" title="Mercurial" style="float: right;">Mercurial</a>
<a href="%(urlbase)s%(url)s">%(reponame)s</a>
</div>
<div><a  class="title" href="%(urlbase)s/shortlog">pushed changes</a></div>
<table cellspacing="0">
<tr><th></th><th>Changeset</th><th>Who</th><th>Files</th><th>Description</th></tr>
""" % {'urlbase': urlbase,
       'url': req.url,
       'reponame': reponame}];

    i = 0
    for node, user, date in e:
        ctx = web.repo.changectx(node)
        resp.append("""<tr class="parity%(i)d"><td class="link"><a href="rev/%(node)s">diff</a><br><a href="file/%(node)s">browse</a></td><td class="age">%(node)s<br/><i>%(date)s</i></td><td><strong>%(user)s</strong></td><td>%(files)s</td><td>%(description)s</td></tr>
""" % {'node': short(bin(node)),
       'date': date,
       'user': xmlescape(user),
       'files': '<br/>'.join(ctx.files()),
       'description': xmlescape(ctx.description()),
       'urlbase': urlbase,
       'url': req.url,
       'i': i})
        i += 1
        i %= 2

    resp.append("""</table>
<div class="page_footer">
<div class="page_footer_text">%(reponame)s</div>
<br />
</div>
</body>
</html>
""" % {'reponame': reponame})

    resp = "".join(resp)

    req.respond(HTTP_OK, "text/html", length=len(resp))
    req.write(resp)

addwebcommand(pushlogFeed, 'pushlog')
addwebcommand(pushlogHTML, 'pushloghtml')

cmdtable = {}
