import mercurial.hgweb.protocol as hgwebprotocol
import mercurial.hgweb.webcommands as hgwebcommands
import mercurial.hgweb.webutil as webutil
from mercurial.templatefilters import xmlescape
from mercurial.hgweb.common import HTTP_OK, HTTP_NOT_FOUND, HTTP_SERVER_ERROR, paritygen
from mercurial.node import short, bin, hex, nullid
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
ACL_HEADER = 'Access-Control-Allow-Origin', '*'

# just an enum
class QueryType:
    DATE, CHANGESET, PUSHID, COUNT = range(4)

class PushlogQuery:
    page = 1
    dates = []
    entries = []
    totalentries = 1
    # by default, we return the last 10 pushes
    querystart = QueryType.COUNT
    querystart_value = PUSHES_PER_PAGE
    # don't need a default here, since by default
    # we'll get everything newer than whatever your start
    # query is
    queryend = None
    queryend_value = None
    # Allow query-by-user
    userquery = []
    # Allow query-by-individual-changeset
    changesetquery = []

    def __init__(self, repo, dbconn, urlbase='', tipsonly=False, reponame=''):
        self.repo = repo
        self.conn = dbconn
        self.urlbase = urlbase
        self.tipsonly = tipsonly
        self.reponame = reponame

    def DoQuery(self):
        """Figure out what the query parameters are, and query the database
        using those parameters."""
        self.entries = []
        if not self.conn:
            # we didn't get a connection to the database, return empty
            return
        if self.querystart == QueryType.COUNT and not self.userquery and not self.changesetquery:
            # Get entries from self.page, using self.querystart_value as
            # the number of pushes per page.
            try:
                res = self.conn.execute("SELECT id, user, date FROM pushlog ORDER BY date DESC LIMIT ? OFFSET ?",
                                        (self.querystart_value,
                                         (self.page - 1) * self.querystart_value))
                for (id,user,date) in res:
                    limit = ""
                    if self.tipsonly:
                        limit = " LIMIT 1"
                    res2 = self.conn.execute("SELECT node FROM changesets WHERE pushid = ? ORDER BY rev DESC" + limit, (id,))
                    for node, in res2:
                        self.entries.append((id,user,date,node))
                # get count of pushes
                self.totalentries = self.conn.execute("SELECT COUNT(*) FROM pushlog").fetchone()[0]
            except sqlite.OperationalError:
                # likely just an empty db, so return an empty result
                pass
        else:
            # for all other queries we'll build the query piece by piece
            basequery = "SELECT id, user, date, node from pushlog LEFT JOIN changesets ON id = pushid WHERE "
            where = []
            params = {}
            if self.querystart == QueryType.DATE:
                where.append("date > :start_date")
                params['start_date'] = self.querystart_value
            elif self.querystart == QueryType.CHANGESET:
                where.append("id > (select c.pushid from changesets c where c.node = :start_node)")
                params['start_node'] = hex(self.repo.lookup(self.querystart_value))
            elif self.querystart == QueryType.PUSHID:
                where.append("id > :start_id")
                params['start_id'] = self.querystart_value

            if self.queryend == QueryType.DATE:
                where.append("date < :end_date ")
                params['end_date'] = self.queryend_value
            elif self.queryend == QueryType.CHANGESET:
                where.append("id <= (select c.pushid from changesets c where c.node = :end_node)")
                params['end_node'] = hex(self.repo.lookup(self.queryend_value))
            elif self.queryend == QueryType.PUSHID:
                where.append("id <= :end_id ")
                params['end_id'] = self.queryend_value

            if self.userquery:
                i = 0
                subquery = []
                for u in self.userquery:
                    subquery.append("user = :user%d" % i)
                    params['user%d' % i] = u
                    i += 1
                where.append('(' + ' OR '.join(subquery) + ')')

            if self.changesetquery:
                i = 0
                subquery = []
                for c in self.changesetquery:
                    subquery.append("id = (select c.pushid from changesets c where c.node = :node%s)" % i)
                    params['node%d' % i] = hex(self.repo.lookup(c))
                    i += 1
                where.append('(' + ' OR '.join(subquery) + ')')
            
            query = basequery + ' AND '.join(where) + ' ORDER BY id DESC, rev DESC'
            #print "query: %s" % query
            #print "params: %s" % params
            try:
                res = self.conn.execute(query, params)
                lastid = None
                for (id, user, date, node) in res:
                    if self.tipsonly and id == lastid:
                        continue
                    self.entries.append((id,user,date,node))
                    lastid = id
            except sqlite.OperationalError:
                # likely just an empty db, so return an empty result
                pass

    def description(self):
        if self.querystart == QueryType.COUNT and not self.userquery and not self.changesetquery:
            return ''
        bits = []
        isotime = lambda x: datetime.fromtimestamp(x).isoformat(' ')
        if self.querystart == QueryType.DATE:
            bits.append('after %s' % isotime(self.querystart_value))
        elif self.querystart == QueryType.CHANGESET:
            bits.append('after changeset %s' % self.querystart_value)
        elif self.querystart == QueryType.PUSHID:
            bits.append('after push ID %s' % self.querystart_value)

        if self.queryend == QueryType.DATE:
            bits.append('before %s' % isotime(self.queryend_value))
        elif self.queryend == QueryType.CHANGESET:
            bits.append('up to and including changeset %s' % self.queryend_value)
        elif self.queryend == QueryType.PUSHID:
            bits.append('up to and including push ID %s' % self.queryend_value)

        if self.userquery:
            bits.append('by user %s' % ' or '.join(self.userquery))

        if self.changesetquery:
            bits.append('with changeset %s' % ' and '.join(self.changesetquery))

        return 'Changes pushed ' + ', '.join(bits)

def localdate(ts):
    """Given a timestamp, return a (timestamp, tzoffset) tuple,
    which is what Mercurial works with. Attempts to get DST
    correct as well."""
    t = time.localtime(ts)
    offset = time.timezone
    if t[8] == 1:
        offset = time.altzone
    return (ts, offset)

def doParseDate(datestring):
    """Given a date string, try to parse it as an ISO 8601 date.
    If that fails, try parsing it with the parsedatetime module,
    which can handle relative dates in natural language."""
    datestring = datestring.strip()
    # This is sort of awful. Match YYYY-MM-DD hh:mm:ss, with the time parts all being optional
    m = re.match("^(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)(?: (?P<hour>\d\d)(?::(?P<minute>\d\d)(?::(?P<second>\d\d))?)?)?$", datestring)
    if m:
        date = (int(m.group("year")), int(m.group("month")), int(m.group("day")),
                m.group("hour") and int(m.group("hour")) or 0,
                m.group("minute") and int(m.group("minute")) or 0,
                m.group("second") and int(m.group("second")) or 0,
                0, # weekday
                0, # yearday
                -1) # isdst
    else:
        # fall back to parsedatetime
        date, x = cal.parse(datestring)
    return time.mktime(date)

def pushlogSetup(repo, req):
    """Given a repository object and a hgweb request object,
    build a PushlogQuery object and populate it with data from the request.
    The returned query object will have its query already run, and
    its entries member can be read."""
    repopath = os.path.dirname(repo.path)
    reponame = os.path.basename(repopath)
    if reponame == '.hg':
        reponame = os.path.basename(os.path.dirname(repopath))
    pushdb = os.path.join(repo.path, "pushlog2.db")
    try:
        conn = sqlite.connect(pushdb)
    except sqlite.OperationalError:
        conn = None

    if 'node' in req.form:
        page = int(req.form['node'][0])
    else:
        page = 1

    # figure out the urlbase
    proto = req.env.get('wsgi.url_scheme')
    if proto == 'https':
        proto = 'https'
        default_port = "443"
    else:
        proto = 'http'
        default_port = "80"
    port = req.env["SERVER_PORT"]
    port = port != default_port and (":" + port) or ""

    tipsonly = False
    if 'tipsonly' in req.form and req.form['tipsonly'][0] == '1':
        tipsonly = True

    query = PushlogQuery(urlbase='%s://%s%s' % (proto, req.env['SERVER_NAME'], port),
                         repo=repo,
                         dbconn=conn,
                         tipsonly=tipsonly,
                         reponame=reponame)
    query.page = page

    # find start component
    if 'startdate' in req.form:
        startdate = doParseDate(req.form['startdate'][0])
        query.querystart = QueryType.DATE
        query.querystart_value = startdate
    elif 'fromchange' in req.form:
        query.querystart = QueryType.CHANGESET
        query.querystart_value = req.form.get('fromchange', ['null'])[0]
    elif 'startID' in req.form:
        query.querystart = QueryType.PUSHID
        query.querystart_value = req.form.get('startID', ['0'])[0]
    else:
        # default is last 10 pushes
        query.querystart = QueryType.COUNT
        query.querystart_value = PUSHES_PER_PAGE

    if 'enddate' in req.form:
        enddate = doParseDate(req.form['enddate'][0])
        query.queryend = QueryType.DATE
        query.queryend_value = enddate
    elif 'tochange' in req.form:
        query.queryend = QueryType.CHANGESET
        query.queryend_value = req.form.get('tochange', ['default'])[0]
    elif 'endID' in req.form:
        query.queryend = QueryType.PUSHID
        query.queryend_value = req.form.get('endID', [None])[0]

    if 'user' in req.form:
        query.userquery = req.form.get('user', [])

    #TODO: use rev here, switch page to ?page=foo ?
    if 'changeset' in req.form:
        query.changesetquery = req.form.get('changeset', [])

    query.DoQuery()
    return query

def pushlogFeed(web, req, tmpl):
    """WebCommand for producing the ATOM feed of the pushlog."""
    
    req.form['style'] = ['atom']
    tmpl = web.templater(req)
    query = pushlogSetup(web.repo, req)
    isotime = lambda x: datetime.utcfromtimestamp(x).isoformat() + 'Z'
    
    if query.entries:
        dt = isotime(query.entries[0][2])
    else:
        dt = datetime.utcnow().isoformat().split('.', 1)[0] + 'Z'

    data = {
        'urlbase': query.urlbase,
        'url': req.url,
        'repo': query.reponame,
        'date': dt,
        'entries': [],
    }

    entries = data['entries']
    for id, user, date, node in query.entries:
        ctx = web.repo.changectx(node)
        entries.append({
            'node': node,
            'date': isotime(date),
            'user': xmlescape(user),
            'urlbase': query.urlbase,
            'url': req.url,
            'files': [{'name': fn} for fn in ctx.files()],
        })

    req.header([ACL_HEADER])
    req.respond(HTTP_OK, ATOM_MIMETYPE)
    return tmpl('pushlog', **data)

def pushlogHTML(web, req, tmpl):
    """WebCommand for producing the HTML view of the pushlog."""
    query = pushlogSetup(web.repo, req)

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
        numpages = int(ceil(query.totalentries / float(PUSHES_PER_PAGE)))
        start = max(1, query.page - PUSHES_PER_PAGE/2)
        end = min(numpages + 1, query.page + PUSHES_PER_PAGE/2)
        if query.page != 1:
            nav.append({'page': 1, 'label': "First"})
            nav.append({'page': query.page - 1, 'label': "Prev"})
        for i in range(start, end):
            nav.append({'page': i, 'label': str(i)})
        
        if query.page != numpages:
            nav.append({'page': query.page + 1, 'label': "Next"})
            nav.append({'page': numpages, 'label': "Last"})
        return nav

    def changelist(limit=0, **map):
        # useless fallback
        listfilediffs = lambda a,b,c: []
        if hasattr(webutil, 'listfilediffs'):
            listfilediffs = lambda a,b,c: webutil.listfilediffs(a,b,c, len(b))
        elif hasattr(web, 'listfilediffs'):
            listfilediffs = web.listfilediffs

        allentries = []
        lastid = None
        ch = None
        l = []
        mergehidden = ""
        p = 0
        currentpush = None
        for id, user, date, node in query.entries:
            ctx = web.repo.changectx(node)
            n = ctx.node()
            entry = {"author": ctx.user(),
                     "desc": ctx.description(),
                     "files": listfilediffs(tmpl, ctx.files(), n),
                     "rev": ctx.rev(),
                     "node": hex(n),
                     "tags": nodetagsdict(web.repo, n),
                     "branches": nodebranchdict(web.repo, ctx),
                     "inbranch": nodeinbranch(web.repo, ctx),
                     "hidden": "",
                     "push": [],
                     "mergerollup": [],
                     "id": id
                     }
            if id != lastid:
                lastid = id
                p = parity.next()
                entry["push"] = [{"user": user,
                                  "date": localdate(date)}]
                if len([c for c in ctx.parents() if c.node() != nullid]) > 1:
                    mergehidden = "hidden"
                    entry["mergerollup"] = [{"count": 0}]
                else:
                    mergehidden = ""
                currentpush = entry
            else:
                entry["hidden"] = mergehidden
                if mergehidden:
                    currentpush["mergerollup"][0]["count"] += 1
            entry["parity"] = p
            l.append(entry)

        if limit > 0:
            l = l[:limit]

        for e in l:
            yield e

    parity = paritygen(web.stripecount)

    req.header([ACL_HEADER])
    return tmpl('pushlog',
                changenav=changenav(),
                rev=0,
                entries=lambda **x: changelist(limit=0,**x),
                latestentry=lambda **x: changelist(limit=1,**x),
                startdate='startdate' in req.form and req.form['startdate'][0] or '1 week ago',
                enddate='enddate' in req.form and req.form['enddate'][0] or 'now',
                querydescription=query.description(),
                archives=web.archivelist("tip"))

def pushes_worker(query):
    """Given a PushlogQuery, return a data structure mapping push IDs
    to a map of data about the push."""
    pushes = {}
    for id, user, date, node in query.entries:
        if id in pushes:
            # we get the pushes in reverse order
            pushes[id]['changesets'].insert(0, node)
        else:
            pushes[id] = {'user': user,
                          'date': date,
                          'changesets': [node]
                          }
    return pushes

def pushes(web, req, tmpl):
    """WebCommand to return a data structure containing pushes."""
    query = pushlogSetup(web.repo, req)
    req.header([ACL_HEADER])
    return tmpl('pushes', data=pushes_worker(query))

def printpushlog(ui, repo, *args):
    """HG Command to print the pushlog data in JSON format."""
    from hgwebjson import HGJSONEncoder
    e = HGJSONEncoder()
    startID = len(args) and args[0] or 0
    endID = len(args) > 1 and args[1] or None
    try:
        conn = sqlite.connect(os.path.join(repo.path, 'pushlog2.db'))
    except sqlite.OperationalError:
        conn = None
    query = PushlogQuery(repo=repo, dbconn=conn)
    query.querystart = QueryType.PUSHID
    query.querystart_value = startID
    if endID is not None:
        query.queryend = QueryType.PUSHID
        query.queryend_value = endID
    query.DoQuery()
    print e.encode(pushes_worker(query))

addwebcommand(pushlogFeed, 'pushlog')
addwebcommand(pushlogHTML, 'pushloghtml')
addwebcommand(pushes, 'pushes')

cmdtable = {
    'printpushlog': (printpushlog, [], "hg printpushlog [startID [endID]]"),
}
