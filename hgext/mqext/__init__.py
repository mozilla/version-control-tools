'''tweaks for the mq extension

Note that many if not all of these changes should really be made to the
upstream project. I just haven't gotten around to it.

Commands added:

  :qshow: Display a single patch (similar to 'export')
  :qtouched: See what patches modify which files

Commands not related to mq:

  :reviewers: Suggest potential reviewers for a patch
  :bugs: Display the bugs that have touched the same files as a patch
  :components: Suggest a potential component for a patch
  :urls: Guess revision urls for pushed changes

Autocommit:

If you would like to have any change to your patch repository committed to
revision control, mqext adds -Q and -M flags to all mq commands that modify the
patch repository. -Q commits the change to the patch repository, and -M sets
the log message used for that commit (but mqext provides reasonable default
messages, tailored to the specific patch repo-modifying command.)

The -M option argument may include a variety of substitution characters after '%' signs:

  :%a: The action being performed (DELETE,REFRESH,NEW,etc.)
  :%p: The name of the patch
  :%n: The new name of the patch (only for qrename/qmv)
  :%s: Diffstat output (only for qrefresh)
  :%P: A string eg "3 patches - change1, change2, change3" summarizing a set of patches
  :%Q: The qparent and qtip revisions after performing the operation

In addition, for commands that take a set of patches (currently only
qdelete/qrm), square brackets may be used to repeatedly '%p' in a substring
with each patch name in turn. So "foo\n[%a: %p\n]bar", for example, with 3
patches would produce::

  foo
  DELETE: change1
  DELETE: change2
  DELETE: change3
  bar

Pretty horrible, huh?

The following commands are modified:

  - qrefresh
  - qnew
  - qrename
  - qdelete
  - qimport
  - qfinish
  - qfold
  - qcrecord (from the crecord extension)

The expected usage is to add the 'mqcommit=auto' option to the 'mqext' section
of your ~/.hgrc so that all changes are autocommitted if you are using a
versioned patch queue, and to do nothing if not::

  [mqext]
  mqcommit = auto

You could also set it to 'yes' to force it to try to commit all changes, and
error out if you don't have (or have forgotten to create) a patch repository.

Alternatively, if you only want a subset of commands to autocommit, you may add
the -Q option to all relevant commands in your ~/.hgrc::

  [defaults]
  qnew = -Q
  qdelete = -Q
  qimport = -Q
'''

import os
from subprocess import call, check_call
import errno
from mercurial.i18n import _
from mercurial.node import hex, nullrev, nullid, short
from mercurial import commands, util, cmdutil, mdiff, error, url, patch, extensions

from hgext import mq
import re
from collections import Counter
import json
import urllib2

try:
    # hg 1.9+
    from mercurial.scmutil import canonpath
except:
    from mercurial.util import canonpath

bugzilla_jsonrpc_url = "https://bugzilla.mozilla.org/jsonrpc.cgi"

def qshow(ui, repo, patchspec=None, **opts):
    '''display a patch

    If no patch is given, the top of the applied stack is shown.'''
    q = repo.mq

    p = q.lookup(patchspec or 'qtip')
    patchf = q.opener(p, "r")

    if opts['stat']:
        del opts['stat']
        lines = patch.diffstatui(patchf, **opts)
    else:
        def singlefile(*a, **b):
            return patchf
        lines = patch.difflabel(singlefile, **opts)

    for chunk, label in lines:
        ui.write(chunk, label=label)

    patchf.close()

def fullpaths(ui, repo, paths):
    cwd = os.getcwd()
    return [ canonpath(repo.root, cwd, path) for path in paths ]

def patch_changes(ui, repo, patchfile=None, **opts):
    '''Given a patch, look at what files it changes, and map a function over
    the changesets that touch overlapping files.

    Scan through the last LIMIT commits to find the relevant changesets

    The patch may be given as a file or a URL. If no patch is specified,
    the changes in the working directory will be used. If there are no
    changes, the topmost applied patch in your mq repository will be used.

    Alternatively, the -f option may be used to pass in one or more files
    that will be used directly.
    '''

    changes = {}

    if opts['file']:
        changedFiles = fullpaths(ui, repo, opts['file'])
    else:
        if patchfile is None:
            # we should use the current diff, or if that is empty, the top
            # applied patch in the patch queue
            ui.pushbuffer()
            commands.diff(ui, repo, git=True)
            diff = ui.popbuffer()
            changedFiles = fileRe.findall(diff)
            if len(changedFiles) > 0:
                source = "current diff"
            elif repo.mq:
                source = "top patch in mq queue"
                ui.pushbuffer()
                try:
                    commands.diff(ui, repo, change="qtip", git=True)
                except error.RepoLookupError, e:
                    raise util.Abort("no current diff, no mq patch to use")
                diff = ui.popbuffer()
            else:
                raise util.Abort("no changes found")
        else:
            try:
                diff = url.open(ui, patchfile).read()
                source = "patch file %s" % patchfile
            except IOError, e:
                q = repo.mq
                if q:
                    diff = url.open(ui, q.lookup(patchfile)).read()
                    source = "mq patch %s" % patchfile
                else:
                    pass

        changedFiles = fileRe.findall(diff)
        if ui.verbose:
            ui.write("Patch source: %s\n" % source)
        if len(changedFiles) == 0:
            ui.write("Warning: no modified files found in patch. Did you mean to use the -f option?\n")

    if ui.verbose:
        ui.write("Using files:\n")
        if len(changedFiles) == 0:
            ui.write("  (none)\n")

    for changedFile in changedFiles:
        changes[changedFile] = []
        if ui.verbose:
            ui.write("  %s\n" % changedFile)

    limit = opts['limit']
    if limit == 0 or len(repo) < limit:
        start = 1
    else:
        start = len(repo) - limit

    for revNum in xrange(start, len(repo)):
        ui.progress("scanning revisions", revNum - start, item=revNum,
                    total=len(repo) - start)
        rev = repo[revNum]
        for file in changedFiles:
            if file in rev.files():
                changes[file].append(rev)

    ui.progress("scanning revisions", None)

    for file in changes:
        for change in changes[file]:
            yield change

fileRe = re.compile(r"^\+\+\+ (?:b/)?([^\s]*)", re.MULTILINE)
suckerRe = re.compile(r"[^s-]r=(\w+)")
supersuckerRe = re.compile(r"sr=(\w+)")

def reviewers(ui, repo, patchfile=None, **opts):
    '''Suggest a reviewer for a patch

    Scan through the last LIMIT commits to find candidate reviewers for a
    patch (or set of files).

    The patch may be given as a file or a URL. If no patch is specified,
    the changes in the working directory will be used. If there are no
    changes, the topmost applied patch in your mq repository will be used.

    Alternatively, the -f option may be used to pass in one or more files
    that will be used to infer the reviewers instead.

    The [reviewers] section of your .hgrc may be used to specify reviewer
    aliases in case reviewers are specified multiple ways.

    Written by Blake Winton http://weblog.latte.ca/blake/
    '''

    def canon(reviewer):
        reviewer = reviewer.lower()
        return ui.config('reviewers', reviewer, reviewer)

    suckers = Counter()
    supersuckers = Counter()
    for change in patch_changes(ui, repo, patchfile, **opts):
        suckers.update(canon(x) for x in suckerRe.findall(change.description()))
        supersuckers.update(canon(x) for x in supersuckerRe.findall(change.description()))

    ui.write("Potential reviewers:\n")
    if (len(suckers) == 0):
        ui.write("  none found in range (try higher --limit?)\n")
    else:
        for (reviewer, count) in suckers.most_common(10):
            ui.write("  %s: %d\n" % (reviewer, count))
    ui.write("\n")

    ui.write("Potential super-reviewers:\n")
    if (len(supersuckers) == 0):
        ui.write("  none found in range (try higher --limit?)\n")
    else:
        for (reviewer, count) in supersuckers.most_common(10):
            ui.write("  %s: %d\n" % (reviewer, count))
 
# This is stolen from bzexport.py, which stole it from buglink.py
# Tweaked slightly to avoid grabbing bug numbers from the beginning of SHA-1s
bug_re = re.compile(r'''# bug followed by any sequence of numbers, or
                        # a standalone sequence of numbers
                     (
                        (?:
                          bug |
                          b= |
                          # a sequence of 5+ numbers preceded by whitespace
                          (?=\b\#?\d{5,}\b) |
                          # numbers at the very beginning
                          ^(?=\d+\b)
                        )
                        (?:\s*\#?)(\d+)
                     )''', re.I | re.X)

def fetch_bugs(url, ui, bugs):
    data = json.dumps({
            "method": "Bug.get",
            "id": 1,
            "permissive": True,
            "include_fields": ["id", "url", "summary", "component", "product" ],
            "params": [{ "ids": list(bugs) }]
    })

    req = urllib2.Request(url,
                          data,
                          { "Accept": "application/json",
                           "Content-Type": "application/json"})

    conn = urllib2.urlopen(req)
    ui.debug("fetched %s for bugs %s\n" % (conn.geturl(), ",".join(bugs)))
    try:
        buginfo = json.load(conn)
    except Exception, e:
        pass

    if buginfo.get('result', None) is None:
        # Error handling: bugzilla will report a single error if any of the
        # retrieved bugs was problematic, so drop that bug and retry with two
        # remaining halves (it'll still do one fetch per failure in the bug
        # range, but presumably fetching N/2 bugs is faster than fetching N so
        # the total time will be less)
        if 'error' in buginfo:
            badbug = None
            m = re.search(r'Bug #(\d+) does not exist', buginfo['error']['message'])
            if m:
                if ui.verbose:
                    ui.write("  dropping nonexistent bug %s\n" % m.group(1))
                badbug = m.group(1)
            m = re.search(r'You are not authorized to access bug #(\d+)', buginfo['error']['message'])
            if m:
                if ui.verbose:
                    ui.write("  dropping inaccessible bug %s\n" % m.group(1))
                badbug = m.group(1)
            bugs.remove(badbug)
            nparts = 2
            if len(bugs) < nparts:
                parts = [ bugs ]
            else:
                bs = list(bugs)
                parts = [ bs[i:len(bugs):nparts] for i in range(0,nparts) ]
            return reduce(lambda bs,p: bs + fetch_bugs(url, ui, p), parts, [])

        raise util.Abort("Failed to retrieve bugs, last buginfo=%r" % (buginfo,))

    return buginfo['result']['bugs']

def bzcomponents(ui, repo, patchfile=None, **opts):
    '''Suggest a bugzilla product and component for a patch

    Scan through the last LIMIT commits to find bug product/components that
    touch the same files.

    The patch may be given as a file or a URL. If no patch is specified,
    the changes in the working directory will be used. If there are no
    changes, the topmost applied patch in your mq repository will be used.

    Alternatively, the -f option may be used to pass in one or more files
    that will be used to infer the component instead.
    '''

    bugs = set()
    for change in patch_changes(ui, repo, patchfile, **opts):
        m = bug_re.search(change.description())
        if m:
            bugs.add(m.group(2))

    components = Counter()
    url = ui.config('bugzilla', 'jsonrpc-url', None)
    if url is None:
        url = ui.config('bugzilla', 'url', None)
        if url is None:
            url = bugzilla_jsonrpc_url
        else:
            url = "%s/jsonrpc.cgi" % url

    for b in fetch_bugs(url, ui, bugs):
        comp = "%s/%s" % (b['product'], b['component'])
        ui.debug("bug %s: %s\n" % (b['id'], comp))
        components.update([comp])

    ui.write("Potential components:\n")
    if len(components) == 0:
        ui.write("  none found in range (try higher --limit?)\n")
    else:
        for (comp, count) in components.most_common(5):
            ui.write("  %s: %d\n" % (comp, count))

def bzbugs(ui, repo, patchfile=None, **opts):
    '''List the bugs that have modified the files in a patch

    Scan through the last LIMIT commits to find bugs that touch the same files.

    The patch may be given as a file or a URL. If no patch is specified,
    the changes in the working directory will be used. If there are no
    changes, the topmost applied patch in your mq repository will be used.

    Alternatively, the -f option may be used to pass in one or more files
    that will be used instead.
    '''

    bugs = set()
    for change in patch_changes(ui, repo, patchfile, **opts):
        m = bug_re.search(change.description())
        if m:
            bugs.add(m.group(2))

    if bugs:
        for bug in bugs:
            ui.write("bug %s\n" % bug)
    else:
        ui.write("No bugs found\n")

def touched(ui, repo, sourcefile=None, **opts):
    '''Show what files are touched by what patches

    If no file is given, print out a series of lines containing a
    patch and a file changed by that patch, for all files changed by
    all patches. This is mainly intended for easy grepping.

    If a file is given, print out the list of patches that touch that file.'''

    q = repo.mq

    if opts['patch'] and opts['applied']:
        raise util.Abort(_('Cannot use both -a and -p options'))

    if opts['patch']:
        patches = [ q.lookup(opts['patch']) ]
    elif opts['applied']:
        patches = [ p.name for p in q.applied ]
    else:
        patches = q.series

    for patchname in [ q.lookup(p) for p in patches ]:
        lines = q.opener(patchname)
        for filename, adds, removes, isbinary in patch.diffstatdata(lines):
            if sourcefile is None:
                ui.write(patchname + "\t" + filename + "\n")
            elif sourcefile == filename:
                ui.write(patchname + "\n")

def mqcommit_info(ui, repo, opts):
    mqcommit = opts.pop('mqcommit', None)

    try:
        auto = ui.configbool('mqext', 'qcommit', None)
        if auto is None:
            raise error.ConfigError()
    except error.ConfigError:
        auto = ui.config('mqext', 'qcommit', 'auto').lower()

    if mqcommit is None and auto:
        if auto == 'auto':
            if repo.mq and repo.mq.qrepo():
                mqcommit = True
        else:
            mqcommit = True

    if mqcommit is None:
        return (None, None, None)

    q = repo.mq
    if q is None:
        raise util.Abort("-Q option given but mq extension not installed")
    r = q.qrepo()
    if r is None:
        raise util.Abort("-Q option given but patch directory is not versioned")

    return mqcommit, q, r

def mqmessage_rep(ch, repo, values):
    if ch in values:
        r = values[ch]
        return r(repo, values) if callable(r) else r
    else:
        raise util.Abort("Invalid substitution %%%s in mqmessage template" % ch)

def queue_info_string(repo, values):
    qparent_str = ''
    qtip_str = ''
    try:
        qparent_str = short(repo.lookup('qparent'))
        qtip_str = short(repo.lookup('qtip'))
    except error.RepoLookupError:
        qparent_str = short(repo.lookup('.'))
        qtip_str = qparent_str
    try:
        top_str = repo.mq.applied[-1].name
    except:
        top_str = '(none)'
    return '\nqparent: %s\nqtip: %s\ntop: %s' % (qparent_str, qtip_str, top_str)

def substitute_mqmessage(s, repo, values):
    newvalues = values.copy()
    newvalues['Q'] = queue_info_string
    s = re.sub(r'\[(.*)\]', lambda m: mqmessage_listrep(m.group(1), repo, newvalues), s, flags = re.S)
    s = re.sub(r'\%(\w)', lambda m: mqmessage_rep(m.group(1), repo, newvalues), s)
    return s

def mqmessage_listrep(message, repo, values):
    newvalues = values.copy()
    s = ''
    for patchname in values['[]']:
        newvalues['p'] = patchname
        s += substitute_mqmessage(message, repo, newvalues)
    return s

# Monkeypatch qrefresh in mq command table
#
# Note: The default value of the parameter is set here because it contains a
# newline, which messes up the formatting of the help message
def qrefresh_wrapper(orig, self, repo, *pats, **opts):
    mqmessage = opts.pop('mqmessage', '') or '%a: %p\n%s%Q'
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    diffstat = ""
    if mqcommit and mqmessage:
        if mqmessage.find("%s") != -1:
            self.pushbuffer()
            m = cmdutil.matchmod.match(repo.root, repo.getcwd(), [],
                                       opts.get('include'), opts.get('exclude'),
                                       'relpath', auditor=repo.auditor)
            cmdutil.diffordiffstat(self, repo, mdiff.diffopts(),
                                   repo.dirstate.parents()[0], None, m,
                                   stat=True)
            diffstat = self.popbuffer()

    orig(self, repo, *pats, **opts)

    if mqcommit and len(q.applied) > 0:
        patch = q.applied[-1].name
        if r is None:
            raise util.Abort("no patch repository found when using -Q option")
        mqmessage = substitute_mqmessage(mqmessage, repo, { 'p': patch,
                                                            'a': 'UPDATE',
                                                            's': diffstat })
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qnew in mq command table
def qnew_wrapper(orig, self, repo, patchfn, *pats, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    orig(self, repo, patchfn, *pats, **opts)

    if mqcommit and mqmessage:
        mqmessage = substitute_mqmessage(mqmessage, repo, { 'p': patchfn,
                                                            'a': 'NEW' })
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qimport in mq command table
def qimport_wrapper(orig, self, repo, *filename, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    orig(self, repo, *filename, **opts)

    if mqcommit and mqmessage:
        # FIXME - can be multiple
        if len(filename) == 0:
            try:
                fname = q.fullseries[0]
            except:
                fname = q.full_series[0]
        else:
            fname = filename[0]
        mqmessage = substitute_mqmessage(mqmessage, repo, { 'p': fname,
                                                            'a': 'IMPORT' })
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qrename in mq command table
def qrename_wrapper(orig, self, repo, patch, name=None, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    orig(self, repo, patch, name, **opts)

    if mqcommit and mqmessage:
        if not name:
            name = patch
            patch = q.lookup('qtip')
        mqmessage = substitute_mqmessage(mqmessage, repo, { 'p': patch,
                                                            'n': name,
                                                            'a': 'RENAME' })
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qdelete in mq command table
#
# Note: The default value of the parameter is set here because it contains a
# newline, which messes up the formatting of the help message
def qdelete_wrapper(orig, self, repo, *patches, **opts):
    mqmessage = opts.pop('mqmessage', '') or '%a: %P\n\n[%a: %p\n]%Q'
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    if mqcommit and mqmessage:
        patchnames = [ q.lookup(p) for p in patches ]

    orig(self, repo, *patches, **opts)

    if mqcommit and mqmessage:
        mqmessage = substitute_mqmessage(mqmessage, repo,
                                         { 'a': 'DELETE',
                                           'P': '%d patches - %s' % (len(patches), " ".join(patchnames)),
                                           '[]': patchnames })
        commands.commit(r.ui, r, message=mqmessage)

def urls(ui, repo, *paths, **opts):
    '''Display a list of urls for the last several commits.
    These are merely heuristic guesses and are intended for pasting into
    bugs after landing. If that makes no sense to you, then you are probably
    not the intended audience. It's mainly a Mozilla thing.

    Note that this will display the URL for your default repo, which may very
    well be something local. So you may need to give your outbound repo as
    an argument.
'''

    opts['template'] = '{node|short} {desc|firstline}\n'
    ui.pushbuffer()
    commands.log(ui, repo, **opts)
    lines = ui.popbuffer()
    if len(paths) == 0:
        paths = ['default']
    ui.pushbuffer()
    commands.paths(ui, repo, *paths)
    url = ui.popbuffer().rstrip()
    url = re.sub(r'^\w+', 'http', url)
    url = re.sub(r'(\w|\%|\.|-)+\@', '', url) # Remove usernames
    for line in lines.split('\n'):
        if len(line) > 0:
            rev, desc = line.split(' ', 1)
            ui.write(url + '/rev/' + rev + '\n  ' + desc + '\n\n')

# Monkeypatch qfinish in mq command table
def qfinish_wrapper(orig, self, repo, *revrange, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    orig(self, repo, *revrange, **opts)

    if mqcommit and mqmessage:
        mqmessage = substitute_mqmessage(mqmessage, repo, { })
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qfold in mq command table
def qfold_wrapper(orig, self, repo, *files, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    if mqcommit and mqmessage:
        patchnames = [ q.lookup(p) or p for p in files ]

    orig(self, repo, *files, **opts)

    if mqcommit and mqmessage:
        mqmessage = substitute_mqmessage(mqmessage, repo, { 'a': 'FOLD',
                                                            'n': ", ".join(patchnames),
                                                            'p': q.lookup('qtip') })
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qcrecord in mq command table (note that this comes from the crecord extension)
def qcrecord_wrapper(orig, self, repo, patchfn, *pats, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    orig(self, repo, patchfn, *pats, **opts)

    if mqcommit and mqmessage:
        mqmessage = substitute_mqmessage(mqmessage, repo, { 'p': patchfn,
                                                            'a': 'NEW' })
        commands.commit(r.ui, r, message=mqmessage)

cmdtable = {
    'qshow': (qshow,
              [('', 'stat', None, 'output diffstat-style summary of changes'),
               ],
              ('hg qshow [patch]')),

    'reviewers':
        (reviewers,
         [('f', 'file', [], 'see reviewers for FILE', 'FILE'),
          ('l', 'limit', 10000, 'how many revisions back to scan', 'LIMIT')
          ],
         ('hg reviewers [-f FILE1 -f FILE2...] [-l LIMIT] [PATCH]')),

    'bugs':
        (bzbugs,
         [('f', 'file', [], 'see components for FILE', 'FILE'),
          ('l', 'limit', 10000, 'how many revisions back to scan', 'LIMIT')
          ],
         ('hg bugs [-f FILE1 -f FILE2...] [-l LIMIT] [PATCH]')),

    'components':
        (bzcomponents,
         [('f', 'file', [], 'see components for FILE', 'FILE'),
          ('l', 'limit', 10000, 'how many revisions back to scan', 'LIMIT')
          ],
         ('hg components [-f FILE1 -f FILE2...] [-l LIMIT] [PATCH]')),

    'qtouched':
        (touched,
         [('a', 'applied', None, 'only consider applied patches'),
          ('p', 'patch', '', 'restrict to given patch')
          ],
         ('hg touched [-a] [-p PATCH] [FILE]')),

    'urls':
        (urls,
         [('d', 'date', '', _('show revisions matching date spec'), _('DATE')),
          ('r', 'rev', [], _('show the specified revision or range'), _('REV')),
          ('u', 'user', [], _('revisions committed by user'), _('USER')),
          ] + commands.logopts,
         ('hg urls [-l LIMIT] [NAME]')),
}

def uisetup(ui):
    try:
        mq = extensions.find('mq')
    except KeyError:
        return # mq not loaded at all

    # check whether mq is loaded before mqext. If not, do a nasty hack to set
    # it up first so that mqext can modify what it does and not have the
    # modifications get clobbered. Mercurial really needs to implement
    # inter-extension dependencies.

    aliases, entry = cmdutil.findcmd('init', commands.table)
    if not [ e for e in entry[1] if e[1] == 'mq' ]:
        orig = mq.uisetup
        mq.uisetup = lambda ui: deferred_uisetup(orig, ui, mq)
        return

    uisetup_post_mq(ui, mq)

def deferred_uisetup(orig, ui, mq):
    orig(ui)
    uisetup_post_mq(ui, mq)

def uisetup_post_mq(ui, mq):
    entry = extensions.wrapcommand(mq.cmdtable, 'qrefresh', qrefresh_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', '', 'commit message for patch update')])

    entry = extensions.wrapcommand(mq.cmdtable, 'qnew', qnew_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', '%a: %p%Q', 'commit message for patch creation')])

    entry = extensions.wrapcommand(mq.cmdtable, 'qimport', qimport_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', 'IMPORT: %p%Q', 'commit message for patch import')])

    entry = extensions.wrapcommand(mq.cmdtable, 'qdelete', qdelete_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', '', 'commit message for patch deletion')])

    entry = extensions.wrapcommand(mq.cmdtable, 'qrename', qrename_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', '%a: %p -> %n%Q', 'commit message for patch rename')])

    entry = extensions.wrapcommand(mq.cmdtable, 'qfinish', qfinish_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', 'FINISHED%Q', 'commit message for patch finishing')])

    entry = extensions.wrapcommand(mq.cmdtable, 'qfold', qfold_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', '%a: %p <- %n%Q', 'commit message for patch folding')])

def extsetup():
    try:
        crecord_ext = extensions.find('crecord')
    except KeyError:
        return # crecord not loaded at all

    # check whether qcrecord is loaded before mqext. If not, do a nasty hack to
    # set it up first so that mqext can modify what it does and not have the
    # modifications get clobbered. Mercurial really needs to implement
    # inter-extension dependencies.

    if 'qcrecord' not in crecord_ext.cmdtable:
        orig = crecord_ext.extsetup
        crecord_ext.extsetup = lambda: deferred_extsetup(orig)
        return

    extsetup_post_crecord()

def deferred_extsetup(orig):
    orig()
    extsetup_post_crecord()

def extsetup_post_crecord():
    crecord_ext = extensions.find('crecord')
    entry = extensions.wrapcommand(crecord_ext.cmdtable, 'qcrecord', qcrecord_wrapper)
    entry[1].extend([('Q', 'mqcommit', None, 'commit change to patch queue'),
                     ('M', 'mqmessage', '%a: %p%Q', 'commit message for patch creation')])
