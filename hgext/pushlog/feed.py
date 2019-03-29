from datetime import datetime
from math import ceil
import collections
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
    scmutil,
    templatefilters,
    templateutil,
)

sys.path.append(os.path.dirname(__file__))

with demandimport.deactivated():
    from parsedatetime import parsedatetime as pdt

xmlescape = templatefilters.xmlescape

testedwith = '4.8'
minimumhgversion = '4.8'

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


def isotime(timestamp):
    '''Returns the ISO format of the given timestamp'''
    return datetime.utcfromtimestamp(timestamp).isoformat() + 'Z'


def feedentrygenerator(_context, entries, repo, url, urlbase):
    """Generator of mappings for pushlog feed entries field
    """
    for pushid, user, date, node in entries:
        ctx = scmutil.revsingle(repo, node)
        filesgen = [{'name': fn} for fn in ctx.files()]
        yield {
            'node': node,
            'date': isotime(date),
            'user': xmlescape(user),
            'urlbase': urlbase,
            'url': url,
            'files': templateutil.mappinglist(filesgen),
        }


def pushlog_feed(web):
    """WebCommand for producing the ATOM feed of the pushlog."""
    req = web.req

    req.qsparams['style'] = 'atom'
    # Need to reset the templater instance to use the new style.
    web.tmpl = web.templater(req)

    query = pushlog_setup(web.repo, req)

    if query.entries:
        dt = isotime(query.entries[0][2])
    else:
        dt = datetime.utcnow().isoformat().split('.', 1)[0] + 'Z'

    url = req.apppath or '/'
    if not url.endswith('/'):
        url += '/'

    queryentries = (
        (pushid, user, date, node)
        for (pushid, user, date, node) in query.entries
        if scmutil.isrevsymbol(web.repo, node)
    )

    data = {
        'urlbase': query.urlbase,
        'url': url,
        'repo': query.reponame,
        'date': dt,
        'entries': templateutil.mappinggenerator(feedentrygenerator, args=(queryentries, web.repo, url, query.urlbase)),
    }

    web.res.headers['Content-Type'] = ATOM_MIMETYPE
    return web.sendtemplate('pushlog', **data)


def create_entry(ctx, web, pushid, user, date, node, mergehidden, parity, pushcount=None):
    """Creates an entry to be yielded in the `changelist` generator

    `pushcount` will be non-None when we are generating an entry for the first change
    in a given push
    """
    repo = web.repo
    n = ctx.node()
    ctxfiles = ctx.files()
    firstchange = pushcount is not None

    mergerollupval = templateutil.mappinglist(
        [{'count': pushcount}]
        if firstchange and mergehidden == 'hidden'
        else []
    )

    pushval = templateutil.mappinglist(
        [{"date": localdate(date), "user": user}]
        if firstchange
        else []
    )

    filediffs = webutil.listfilediffs(ctxfiles, node, len(ctxfiles))

    return {
        "author": ctx.user(),
        "desc": ctx.description(),
        "files": filediffs,
        "rev": ctx.rev(),
        "node": hex(n),
        "parents": [c.hex() for c in ctx.parents()],
        "tags": webutil.nodetagsdict(repo, n),
        "branches": webutil.nodebranchdict(repo, ctx),
        "inbranch": webutil.nodeinbranch(repo, ctx),
        "hidden": mergehidden,
        "mergerollup": mergerollupval,
        "id": pushid,
        "parity": parity,
        "push": pushval,
    }


def handle_entries_for_push(web, samepush, p):
    '''Displays pushlog changelist entries for a single push

    The main use of this function is to ensure the first changeset
    for a given push receives extra required information, namely
    the information needed to populate the `mergerollup` and `push`
    fields. These fields are only present on the first changeset in
    a push, and show the number of changesets merged in this push
    (if the push was a merge) and the user who pushed the change,
    respectively.
    '''
    pushcount = len(samepush)

    pushid, user, date, node = samepush.popleft()
    ctx = scmutil.revsingle(web.repo, node)
    multiple_parents = len([c for c in ctx.parents() if c.node() != nullid]) > 1
    mergehidden = "hidden" if multiple_parents else ""

    # Yield the initial entry, which contains special information such as
    # the number of changesets merged in this push
    yield create_entry(ctx, web, pushid, user, date, node, mergehidden, p,
                       pushcount=pushcount)

    # Yield all other entries for the given push
    for pushid, user, date, node in samepush:
        ctx = scmutil.revsingle(web.repo, node)
        yield create_entry(ctx, web, pushid, user, date, node, mergehidden, p,
                           pushcount=None)


def pushlog_changenav(_context, query):
    '''Generator which yields changelist navigation fields for the pushlog
    '''
    numpages = int(ceil(query.totalentries / float(PUSHES_PER_PAGE)))
    start = max(1, query.page - PUSHES_PER_PAGE/2)
    end = min(numpages + 1, query.page + PUSHES_PER_PAGE/2)

    if query.page != 1:
        yield {'page': 1, 'label': "First"}
        yield {'page': query.page - 1, 'label': "Prev"}

    for i in range(start, end):
        yield {'page': i, 'label': str(i)}

    if query.page != numpages:
        yield {'page': query.page + 1, 'label': "Next"}
        yield {'page': numpages, 'label': "Last"}


def pushlog_changelist(_context, web, query, tiponly):
    '''Generator which yields a entries in a changelist for the pushlog
    '''
    parity = paritygen(web.stripecount)
    p = next(parity)

    # Iterate over query entries if we have not reached the limit and
    # the node is visible in the repo
    visiblequeryentries = (
        (pushid, user, date, node)
        for pushid, user, date, node in query.entries
        if scmutil.isrevsymbol(web.repo, node)
    )

    # FIFO queue. Accumulate pushes as we need to
    # count how many entries correspond with a given push
    samepush = collections.deque()

    # Get the first element of the query
    # return if there are no entries
    try:
        pushid, user, date, node = next(visiblequeryentries)

        lastid = pushid
        samepush.append(
            (pushid, user, date, node)
        )
    except StopIteration:
        return

    # Iterate over all the non-hidden entries and aggregate
    # them together per unique pushid
    for allentry in visiblequeryentries:
        pushid, user, date, node = allentry

        # If the entries both come from the same push, add to the accumulated set of entries
        if pushid == lastid:
            samepush.append(allentry)

        # Once the pushid's are different, yield the result
        else:
            # If this is the first changeset for this push, put the change in the queue
            firstpush = len(samepush) == 0

            if firstpush:
                samepush.append(allentry)

            for entry in handle_entries_for_push(web, samepush, p):
                yield entry

                if tiponly:
                    return

            # Set the lastid
            lastid = pushid

            # Swap parity once we are on to processing another push
            p = next(parity)

            # Reset the aggregation of entries, as we are now processing a new push
            samepush = collections.deque()

            # If this was not the first push, the current entry needs processing
            # Add it to the queue here
            if not firstpush:
                samepush.append(allentry)

    # We don't need to display the remaining entries on the page if there are none
    if not samepush:
        return

    # Display the remaining entries for the page
    for entry in handle_entries_for_push(web, samepush, p):
        yield entry

        if tiponly:
            return


def pushlog_html(web):
    """WebCommand for producing the HTML view of the pushlog."""
    req = web.req

    query = pushlog_setup(web.repo, req)

    data = {
        'changenav': templateutil.mappinggenerator(pushlog_changenav, args=(query,)),
        'rev': 0,
        'entries': templateutil.mappinggenerator(pushlog_changelist, args=(web, query, False)),
        'latestentry': templateutil.mappinggenerator(pushlog_changelist, args=(web, query, True)),
        'startdate': req.qsparams.get('startdate', '1 week ago'),
        'enddate': req.qsparams.get('enddate', 'now'),
        'querydescription': query.description(),
        'archives': web.archivelist("tip"),
    }

    return web.sendtemplate('pushlog', **data)


def pushes_worker(query, repo, full):
    """Given a PushlogQuery, return a data structure mapping push IDs
    to a map of data about the push."""
    haveobs = bool(repo.obsstore)
    pushes = {}
    for pushid, user, date, node in query.entries:
        pushid = str(pushid)

        # Create the pushes entry first. It is OK to have empty
        # pushes if nodes from the pushlog no longer exist.
        if pushid not in pushes:
            pushes[pushid] = {
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
                'files': ctx.files(),
            }

            # Only expose obsolescence metadata if the repo has some.
            if haveobs:
                precursors = repo.obsstore.predecessors.get(ctx.node(), ())

                precursors = [hex(m[0]) for m in precursors]
                if precursors:
                    node['precursors'] = precursors

        pushes[pushid].setdefault(nodekey, []).insert(0, node)

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
