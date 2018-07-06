from datetime import datetime
from math import ceil
import os
import re
import sqlite3
import sys
import time

import mercurial.hgweb.webcommands as hgwebcommands
import mercurial.hgweb.webutil as webutil
from mercurial.hgweb.common import (
    ErrorResponse,
    HTTP_OK,
    paritygen,
)
from mercurial.node import hex, nullid
from mercurial import (
    demandimport,
    error,
    templatefilters,
    util,
)

sys.path.append(os.path.dirname(__file__))

with demandimport.deactivated():
    from parsedatetime import parsedatetime as pdt

xmlescape = templatefilters.xmlescape

testedwith = '4.3 4.4 4.5 4.6'
minimumhgversion = '4.3'

cal = pdt.Calendar()
PUSHES_PER_PAGE = 10

def addwebcommand(f, name):
    setattr(hgwebcommands, name, f)
    hgwebcommands.__all__.append(name)

ATOM_MIMETYPE = 'application/atom+xml'


# TRACKING hg46
def qsparam(req, key, default):
    try:
        return req.qsparams.get(key, default)
    except AttributeError:
        return req.form.get(key, [default])[0]


def hasqsparam(req, key):
    try:
        return key in req.qsparams
    except AttributeError:
        return key in req.form


# just an enum
class QueryType:
    DATE, CHANGESET, PUSHID, COUNT = range(4)

class PushlogQuery(object):
    def __init__(self, repo, urlbase='', tipsonly=False):
        self.repo = repo
        self.urlbase = urlbase
        self.tipsonly = tipsonly
        self.reponame = os.path.basename(repo.root)

        self.page = 1
        self.dates = []
        self.entries = []
        self.totalentries = 1
        # by default, we return the last 10 pushes
        self.querystart = QueryType.COUNT
        self.querystart_value = PUSHES_PER_PAGE
        # don't need a default here, since by default
        # we'll get everything newer than whatever your start
        # query is
        self.queryend = None
        self.queryend_value = None
        # Allow query-by-user
        self.userquery = []
        # Allow query-by-individual-changeset
        self.changesetquery = []

        self.formatversion = 1
        # ID of the last known push in the database.
        self.lastpushid = None

    def DoQuery(self, conn):
        """Figure out what the query parameters are, and query the database
        using those parameters."""
        # Use an unfiltered repo because query parameters may reference hidden
        # changesets. Hidden changesets are still in the pushlog. We'll
        # treat them appropriately at the filter layer.
        repo = self.repo.unfiltered()
        self.entries = []
        if not conn:
            # we didn't get a connection to the database, return empty
            return
        if self.querystart == QueryType.COUNT and not self.userquery and not self.changesetquery:
            # Get entries from self.page, using self.querystart_value as
            # the number of pushes per page.
            try:
                res = conn.execute("SELECT id, user, date FROM pushlog ORDER BY id DESC LIMIT ? OFFSET ?",
                                   (self.querystart_value,
                                   (self.page - 1) * self.querystart_value))
                for (id, user, date) in res:
                    limit = ""
                    if self.tipsonly:
                        limit = " LIMIT 1"
                    res2 = conn.execute("SELECT node FROM changesets WHERE pushid = ? ORDER BY rev DESC" + limit, (id,))
                    for node, in res2:
                        self.entries.append((id, user.encode('utf-8'), date, node.encode('utf-8')))
                # get count of pushes
                self.totalentries = conn.execute("SELECT COUNT(*) FROM pushlog").fetchone()[0]
            except sqlite3.OperationalError:
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
                params['start_node'] = hex(repo.lookup(self.querystart_value))
            elif self.querystart == QueryType.PUSHID:
                where.append("id > :start_id")
                params['start_id'] = self.querystart_value

            if self.queryend == QueryType.DATE:
                where.append("date < :end_date ")
                params['end_date'] = self.queryend_value
            elif self.queryend == QueryType.CHANGESET:
                where.append("id <= (select c.pushid from changesets c where c.node = :end_node)")
                params['end_node'] = hex(repo.lookup(self.queryend_value))
            elif self.queryend == QueryType.PUSHID:
                where.append("id <= :end_id ")
                params['end_id'] = self.queryend_value

            if self.userquery:
                subquery = []
                for i, u in enumerate(self.userquery):
                    subquery.append("user = :user%d" % i)
                    params['user%d' % i] = u

                where.append('(' + ' OR '.join(subquery) + ')')

            if self.changesetquery:
                subquery = []
                for i, c in enumerate(self.changesetquery):
                    subquery.append("id = (select c.pushid from changesets c where c.node = :node%s)" % i)
                    params['node%d' % i] = hex(repo.lookup(c))
                where.append('(' + ' OR '.join(subquery) + ')')

            query = basequery + ' AND '.join(where) + ' ORDER BY id DESC, rev DESC'
            try:
                res = conn.execute(query, params)
                lastid = None
                for (id, user, date, node) in res:
                    # Empty push.
                    if not node:
                        continue

                    if self.tipsonly and id == lastid:
                        continue
                    self.entries.append((id, user.encode('utf-8'), date, node.encode('utf-8')))
                    lastid = id
            except sqlite3.OperationalError:
                # likely just an empty db, so return an empty result
                pass

        try:
            query = 'select id from pushlog order by id desc limit 1'
            row = conn.execute(query).fetchone()
            if row:
                self.lastpushid = row[0]
        except sqlite3.OperationalError:
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
    page = int(qsparam(req, 'node', '1'))

    # figure out the urlbase
    # TRACKING hg46
    if util.safehasattr(req, 'urlscheme'):
        proto = req.urlscheme
    else:
        proto = req.env.get('wsgi.url_scheme')

    if proto == 'https':
        proto = 'https'
        default_port = "443"
    else:
        proto = 'http'
        default_port = "80"

    # TRACKING hg46
    if util.safehasattr(req, 'rawenv'):
        port = req.rawenv["SERVER_PORT"]
    else:
        port = req.env["SERVER_PORT"]
    port = port != default_port and (":" + port) or ""

    tipsonly = qsparam(req, 'tipsonly', None) == '1'

    # TRACKING hg46
    if util.safehasattr(req, 'rawenv'):
        urlbase = req.advertisedbaseurl
    else:
        urlbase = '%s://%s%s' % (proto, req.env['SERVER_NAME'], port)

    query = PushlogQuery(urlbase=urlbase,
                         repo=repo,
                         tipsonly=tipsonly)
    query.page = page

    # find start component
    if hasqsparam(req, 'startdate'):
        startdate = doParseDate(qsparam(req, 'startdate', None))
        query.querystart = QueryType.DATE
        query.querystart_value = startdate
    elif hasqsparam(req, 'fromchange'):
        query.querystart = QueryType.CHANGESET
        query.querystart_value = qsparam(req, 'fromchange', None)
    elif hasqsparam(req, 'startID'):
        query.querystart = QueryType.PUSHID
        query.querystart_value = qsparam(req, 'startID', None)
    else:
        # default is last 10 pushes
        query.querystart = QueryType.COUNT
        query.querystart_value = PUSHES_PER_PAGE

    if hasqsparam(req, 'enddate'):
        enddate = doParseDate(qsparam(req, 'enddate', None))
        query.queryend = QueryType.DATE
        query.queryend_value = enddate
    elif hasqsparam(req, 'tochange'):
        query.queryend = QueryType.CHANGESET
        query.queryend_value = qsparam(req, 'tochange', None)
    elif hasqsparam(req, 'endID'):
        query.queryend = QueryType.PUSHID
        query.queryend_value = qsparam(req, 'endID', None)

    # TRACKING hg46
    try:
        query.userquery = req.qsparams.getall('user')
    except AttributeError:
        query.userquery = req.form.get('user', [])

    #TODO: use rev here, switch page to ?page=foo ?
    # TRACKING hg46
    if hasqsparam(req, 'changeset'):
        try:
            query.changesetquery = req.qsparams.getall('changeset')
        except AttributeError:
            query.changesetquery = req.form['changeset']

    try:
        query.formatversion = int(qsparam(req, 'version', '1'))
    except ValueError:
        raise ErrorResponse(500, 'version parameter must be an integer')
    if query.formatversion < 1 or query.formatversion > 2:
        raise ErrorResponse(500, 'version parameter must be 1 or 2')

    with repo.pushlog.conn(readonly=True) as conn:
        query.DoQuery(conn)

    return query

def pushlogFeed(*args):
    """WebCommand for producing the ATOM feed of the pushlog."""

    # TRACKING hg46
    if len(args) == 1:
        web = args[0]
        req = web.req
    else:
        assert len(args) == 3
        web, req = args[0:2]

    # TRACKING hg46
    try:
        req.qsparams['style'] = 'atom'
        # Need to reset the templater instance to use the new style.
        web.tmpl = web.templater(req)
    except AttributeError:
        req.form['style'] = ['atom']

    tmpl = web.templater(req)
    query = pushlogSetup(web.repo, req)
    isotime = lambda x: datetime.utcfromtimestamp(x).isoformat() + 'Z'

    if query.entries:
        dt = isotime(query.entries[0][2])
    else:
        dt = datetime.utcnow().isoformat().split('.', 1)[0] + 'Z'

    # TRACKING hg46
    if util.safehasattr(req, 'apppath'):
        url = req.apppath or '/'
    else:
        url = req.url

    data = {
        'urlbase': query.urlbase,
        'url': url,
        'repo': query.reponame,
        'date': dt,
        'entries': [],
    }

    entries = data['entries']
    for id, user, date, node in query.entries:
        try:
            ctx = web.repo[node]
        # Changeset is hidden.
        except error.FilteredRepoLookupError:
            pass

        entries.append({
            'node': node,
            'date': isotime(date),
            'user': xmlescape(user),
            'urlbase': query.urlbase,
            'url': url,
            'files': [{'name': fn} for fn in ctx.files()],
        })

    # TRACKING hg46
    if util.safehasattr(web, 'sendtemplate'):
        web.res.headers['Content-Type'] = ATOM_MIMETYPE
        return web.sendtemplate('pushlog', **data)
    else:
        req.respond(HTTP_OK, ATOM_MIMETYPE)
        return tmpl('pushlog', **data)


def pushlogHTML(*args):
    """WebCommand for producing the HTML view of the pushlog."""
    # TRACKING hg46
    if len(args) == 1:
        web = args[0]
        req = web.req
        tmpl = web.tmpl
    else:
        assert len(args) == 3
        web, req, tmpl = args

    query = pushlogSetup(web.repo, req)

    # these three functions are in webutil in newer hg, but not in hg 1.0
    def nodetagsdict(repo, node):
        return [{"name": i} for i in repo.nodetags(node)]

    def nodebranchdict(repo, ctx):
        branches = []
        branch = ctx.branch()
        # If this is an empty repo, ctx.node() == nullid,
        # ctx.branch() == 'default', but branchmap is
        # an empty dict. Using dict.get avoids a traceback.
        if repo.branchmap().get(branch) == ctx.node():
            branches.append({'name': branch})
        return branches

    def nodeinbranch(repo, ctx):
        branches = []
        branch = ctx.branch()
        if branch != 'default' and repo.branchmap().get(branch) != ctx.node():
            branches.append({'name': branch})
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

        lastid = None
        l = []
        mergehidden = ""
        p = 0
        currentpush = None
        for id, user, date, node in query.entries:
            if isinstance(node, unicode):
                node = node.encode('utf-8')

            try:
                ctx = web.repo[node]
            # Changeset is hidden.
            except error.FilteredRepoLookupError:
                continue
            n = ctx.node()
            entry = {"author": ctx.user(),
                     "desc": ctx.description(),
                     "files": listfilediffs(tmpl, ctx.files(), n),
                     "rev": ctx.rev(),
                     "node": hex(n),
                     "parents": [c.hex() for c in ctx.parents()],
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

    data = dict(
        changenav=changenav(),
        rev=0,
        entries=lambda **x: changelist(limit=0, **x),
        latestentry=lambda **x: changelist(limit=1, **x),
        startdate=qsparam(req, 'startdate', '1 week ago'),
        enddate=qsparam(req, 'enddate', 'now'),
        querydescription=query.description(),
        archives=web.archivelist("tip")
    )

    # TRACKING hg46
    if util.safehasattr(web, 'sendtemplate'):
        return web.sendtemplate('pushlog', **data)
    else:
        return tmpl('pushlog', **data)


def pushes_worker(query, repo, full):
    """Given a PushlogQuery, return a data structure mapping push IDs
    to a map of data about the push."""
    haveobs = bool(repo.obsstore)
    pushes = {}
    for id, user, date, node in query.entries:
        id = str(id)

        # Create the pushes entry first. It is OK to have empty
        # pushes if nodes from the pushlog no longer exist.
        if id not in pushes:
            pushes[id] = {
                'user': user,
                'date': date,
                'changesets': [],
            }

        try:
            ctx = repo[node]
            nodekey = 'changesets'
        # Changeset is hidden
        except error.FilteredRepoLookupError:
            # Try to find the hidden changeset so its metadata can be used.
            try:
                ctx = repo.unfiltered()[node]
            except error.LookupError:
                continue

            nodekey = 'obsoletechangesets'

        if full:
            node = {
                'node': ctx.hex(),
                'author': ctx.user(),
                'desc': ctx.description(),
                'branch': ctx.branch(),
                'parents': [c.hex() for c in ctx.parents()],
                'tags': ctx.tags(),
                'files': ctx.files()
            }

            # Only expose obsolescence metadata if the repo has some.
            if haveobs:
                # TRACKING hg46
                if util.safehasattr(repo.obsstore, 'predecessors'):
                    precursors = repo.obsstore.predecessors.get(ctx.node(), ())
                else:
                    precursors = repo.obsstore.precursors.get(ctx.node(), ())

                precursors = [hex(m[0]) for m in precursors]
                if precursors:
                    node['precursors'] = precursors

        # we get the pushes in reverse order
        pushes[id].setdefault(nodekey, []).insert(0, node)

    return {'pushes': pushes, 'lastpushid': query.lastpushid}

def pushes(*args):
    """WebCommand to return a data structure containing pushes."""
    # TRACKING hg46
    if len(args) == 1:
        web = args[0]
        req = web.req
        tmpl = web.tmpl
    else:
        assert len(args) == 3
        web, req, tmpl = args

    query = pushlogSetup(web.repo, req)
    data = pushes_worker(query, web.repo, hasqsparam(req, 'full'))

    if query.formatversion == 1:
        template = 'pushes1'
    elif query.formatversion == 2:
        template = 'pushes2'
    else:
        raise ErrorResponse(500, 'unexpected formatversion')

    # TRACKING hg46
    if util.safehasattr(web, 'sendtemplate'):
        return web.sendtemplate(template, **data)
    else:
        return tmpl(template, **data)


addwebcommand(pushlogFeed, 'pushlog')
addwebcommand(pushlogHTML, 'pushloghtml')
addwebcommand(pushes, 'pushes')
