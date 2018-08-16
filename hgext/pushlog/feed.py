from datetime import datetime
from math import ceil
import os
import re
import sys
import time

import mercurial.hgweb.webcommands as hgwebcommands
import mercurial.hgweb.webutil as webutil
from mercurial.hgweb.common import (
    ErrorResponse,
    paritygen,
)
from mercurial.node import hex, nullid
from mercurial import (
    demandimport,
    error,
    templatefilters,
)

sys.path.append(os.path.dirname(__file__))

with demandimport.deactivated():
    from parsedatetime import parsedatetime as pdt

xmlescape = templatefilters.xmlescape

testedwith = '4.6'
minimumhgversion = '4.6'

cal = pdt.Calendar()
PUSHES_PER_PAGE = 10


def addwebcommand(f, name):
    '''Adds `f` as a webcommand named `name`.'''
    setattr(hgwebcommands, name, f)
    hgwebcommands.__all__.append(name)


ATOM_MIMETYPE = 'application/atom+xml'


class QueryType:
    '''Enumeration of the different Pushlog query types'''
    DATE, CHANGESET, PUSHID, COUNT = range(4)


class PushlogQuery(object):
    '''Represents the internal state of a query to Pushlog'''
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

    def do_query(self):
        """Figure out what the query parameters are, and query the database
        using those parameters."""
        # Use an unfiltered repo because query parameters may reference hidden
        # changesets. Hidden changesets are still in the pushlog. We'll
        # treat them appropriately at the filter layer.
        self.entries = []

        if self.querystart == QueryType.COUNT and not self.userquery and not self.changesetquery:
            pushes = self.repo.pushlog.pushes(
                offset=(self.page - 1) * self.querystart_value,
                limit=self.querystart_value,
                reverse=True,
                only_replicated=True,
            )

            for push in pushes:
                if self.tipsonly and push.nodes:
                    nodes = [push.nodes[0]]
                else:
                    nodes = push.nodes

                for node in nodes:
                    self.entries.append(
                        (push.pushid, push.user, push.when, node))

            self.totalentries = self.repo.pushlog.push_count()

        else:
            start_when = None
            start_push_id = None
            end_when = None
            end_push_id = None
            start_node = None
            end_node = None

            if self.querystart == QueryType.DATE:
                start_when = self.querystart_value
            elif self.querystart == QueryType.PUSHID:
                start_push_id = int(self.querystart_value)
            elif self.querystart == QueryType.CHANGESET:
                start_node = self.querystart_value

            if self.queryend == QueryType.DATE:
                end_when = self.queryend_value
            elif self.queryend == QueryType.PUSHID:
                end_push_id = int(self.queryend_value)
            elif self.queryend == QueryType.CHANGESET:
                end_node = self.queryend_value

            pushes = self.repo.pushlog.pushes(
                reverse=True,
                start_id=start_push_id,
                start_id_exclusive=True,
                end_id=end_push_id,
                end_id_exclusive=False,
                start_time=start_when,
                start_time_exclusive=True,
                end_time=end_when,
                end_time_exclusive=True,
                users=self.userquery,
                start_node=start_node,
                start_node_exclusive=True,
                end_node=end_node,
                end_node_exclusive=False,
                nodes=self.changesetquery,
                only_replicated=True,
            )

            for push in pushes:
                if self.tipsonly:
                    nodes = [push.nodes[0]]
                else:
                    nodes = push.nodes

                for node in nodes:
                    self.entries.append((push.pushid, push.user, push.when, node))

        self.lastpushid = self.repo.pushlog.last_push_id_replicated()

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
    return ts, offset


def do_parse_date(datestring):
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


def pushlog_setup(repo, req):
    """Given a repository object and a hgweb request object,
    build a PushlogQuery object and populate it with data from the request.
    The returned query object will have its query already run, and
    its entries member can be read."""
    page = int(req.qsparams.get('node', '1'))

    tipsonly = req.qsparams.get('tipsonly', None) == '1'

    urlbase = req.advertisedbaseurl

    query = PushlogQuery(urlbase=urlbase,
                         repo=repo,
                         tipsonly=tipsonly)
    query.page = page

    # find start component
    if 'startdate' in req.qsparams:
        startdate = do_parse_date(req.qsparams.get('startdate', None))
        query.querystart = QueryType.DATE
        query.querystart_value = startdate
    elif 'fromchange' in req.qsparams:
        query.querystart = QueryType.CHANGESET
        query.querystart_value = req.qsparams.get('fromchange', None)
    elif 'startID' in req.qsparams:
        query.querystart = QueryType.PUSHID
        query.querystart_value = req.qsparams.get('startID', None)
    else:
        # default is last 10 pushes
        query.querystart = QueryType.COUNT
        query.querystart_value = PUSHES_PER_PAGE

    if 'enddate' in req.qsparams:
        enddate = do_parse_date(req.qsparams.get('enddate', None))
        query.queryend = QueryType.DATE
        query.queryend_value = enddate
    elif 'tochange' in req.qsparams:
        query.queryend = QueryType.CHANGESET
        query.queryend_value = req.qsparams.get('tochange', None)
    elif 'endID' in req.qsparams:
        query.queryend = QueryType.PUSHID
        query.queryend_value = req.qsparams.get('endID', None)

    query.userquery = req.qsparams.getall('user')

    #TODO: use rev here, switch page to ?page=foo ?
    query.changesetquery = req.qsparams.getall('changeset')

    try:
        query.formatversion = int(req.qsparams.get('version', '1'))
    except ValueError:
        raise ErrorResponse(500, 'version parameter must be an integer')
    if query.formatversion < 1 or query.formatversion > 2:
        raise ErrorResponse(500, 'version parameter must be 1 or 2')

    query.do_query()

    return query


def pushlog_feed(web):
    """WebCommand for producing the ATOM feed of the pushlog."""
    req = web.req

    req.qsparams['style'] = 'atom'
    # Need to reset the templater instance to use the new style.
    web.tmpl = web.templater(req)

    query = pushlog_setup(web.repo, req)
    isotime = lambda x: datetime.utcfromtimestamp(x).isoformat() + 'Z'

    if query.entries:
        dt = isotime(query.entries[0][2])
    else:
        dt = datetime.utcnow().isoformat().split('.', 1)[0] + 'Z'

    url = req.apppath or '/'
    if not url.endswith('/'):
        url += '/'

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

    web.res.headers['Content-Type'] = ATOM_MIMETYPE
    return web.sendtemplate('pushlog', **data)


def pushlog_html(web):
    """WebCommand for producing the HTML view of the pushlog."""
    req = web.req
    tmpl = web.tmpl

    query = pushlog_setup(web.repo, req)

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
        startdate=req.qsparams.get('startdate', '1 week ago'),
        enddate=req.qsparams.get('enddate', 'now'),
        querydescription=query.description(),
        archives=web.archivelist("tip")
    )

    return web.sendtemplate('pushlog', **data)


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
                precursors = repo.obsstore.predecessors.get(ctx.node(), ())

                precursors = [hex(m[0]) for m in precursors]
                if precursors:
                    node['precursors'] = precursors

        # we get the pushes in reverse order
        pushes[id].setdefault(nodekey, []).insert(0, node)

    return {'pushes': pushes, 'lastpushid': query.lastpushid}


def pushes(web):
    """WebCommand to return a data structure containing pushes."""
    req = web.req

    query = pushlog_setup(web.repo, req)
    data = pushes_worker(query, web.repo, 'full' in req.qsparams)

    if query.formatversion == 1:
        template = 'pushes1'
    elif query.formatversion == 2:
        template = 'pushes2'
    else:
        raise ErrorResponse(500, 'unexpected formatversion')

    return web.sendtemplate(template, **data)


addwebcommand(pushlog_feed, 'pushlog')
addwebcommand(pushlog_html, 'pushloghtml')
addwebcommand(pushes, 'pushes')
