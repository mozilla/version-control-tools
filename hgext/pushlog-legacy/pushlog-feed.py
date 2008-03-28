import mercurial.hgweb.protocol as hgwebprotocol
from mercurial.templatefilters import xmlescape
from mercurial.hgweb.common import HTTP_OK, HTTP_NOT_FOUND, HTTP_SERVER_ERROR
import os.path
import re
import time

def addwebcommand(f, name):
    setattr(hgwebprotocol, name, f)
    hgwebprotocol.__all__.append(name)

datere = re.compile(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4}) (\d{2}):(\d{2}):(\d{2}) -(\d{4})$')

MONTHS = {'Jan': 1,
          'Feb': 2,
          'Mar': 3,
          'Apr': 4,
          'May': 5,
          'Jun': 6,
          'Jul': 7,
          'Aug': 8,
          'Sep': 9,
          'Oct': 10,
          'Nov': 11,
          'Dec': 12}

def rfc3339datehack(dstr):
    wday, d, m, y, h, min, s, tz = datere.match(dstr).groups()

    m = MONTHS[m]
    d = int(d)
    
    return "%s-%02i-%02iT%s:%s:%s-%s:%s" % (
        y, m, d, h, min, s, tz[:2], tz[2:])

ATOM_MIMETYPE = 'application/atom+xml'

reader = re.compile(r'^"([a-f0-9]{40})"\t"([^\t]*)"\t"([^\t]*)"$')

def readlog(logfile):
    """Read a pushlog and yield (node, user, date) for each line."""
    fd = open(logfile)
    entries = []
    for line in fd:
        entries.append(reader.match(line).group(1, 2, 3))
    entries.reverse()
    return entries

def pushlog(web, req):
    plogfile = os.path.join(web.repo.path, "pushlog")
    e = readlog(plogfile)

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

    resp = ["""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <id>%(urlbase)s%(url)spushlog</id>
 <link rel="self" href="%(urlbase)s%(url)spushlog" />
 <updated>%(date)s</updated>
 <title>Pushlog</title>""" % {'urlbase': urlbase,
                              'url': req.url,
                              'date': rfc3339datehack(e[0][2])}];

    for node, user, date in e[:10]:
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
                'date': rfc3339datehack(date),
                'user': xmlescape(user),
                'urlbase': urlbase,
                'url': req.url})

    resp.append("</feed>")

    resp = "".join(resp)

    req.respond(HTTP_OK, ATOM_MIMETYPE, length=len(resp))
    req.write(resp)

addwebcommand(pushlog, 'pushlog')

cmdtable = {}
