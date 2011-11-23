'''tweaks for the mq extension

Note that many if not all of these changes should really be made to the
upstream project. I just haven't gotten around to it.

Commands added:

  :qshow: Display a single patch (similar to 'export')
  :qtouched: See what patches modify which files
  :qbackout: Queue up a backout of a set of changesets

Commands not related to mq:

  :lineage: Dump out the revision history leading up to a particular revision
  :reviewers: Suggest potential reviewers for a patch
  :bugs: Display the bugs that have touched the same files as a patch
  :components: Suggest a potential component for a patch

Autocommit:

If you would like to have any change to your patch repository committed to
revision control, mqext adds -Q and -M flags to all mq commands that modify the
patch repository. -Q commits the change to the patch repository, and -M sets
the log message used for that commit (but mqext provides reasonable default
messages, tailored to the specific patch repo-modifying command, so you'll
rarely use this.)

The following commands are modified:

  - qrefresh
  - qnew
  - qrename
  - qdelete
  - qimport
  - qfinish

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

# TODO:
# [ ] Make 'show' dispatch to export?diff? for eg --stat
#     - Hmm. No. export is all about generating a patch from adjacent revisions
#       We already have a patch.

import os
from subprocess import call, check_call
import errno
from mercurial.i18n import _
from mercurial.node import hex, nullrev, nullid, short
from mercurial import commands, util, cmdutil, mdiff, error, url, patch

# For qbackout
from mercurial import scmutil

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
        s = patch.split(patchf)
        def singlefile(*a, **b):
            return patchf
        lines = patch.difflabel(singlefile, **opts)

    for chunk, label in lines:
        ui.write(chunk, label=label)

    patchf.close()

def lineage(ui, repo, rev='.', limit=None, stop=None, **opts):
    '''Show ancestors of a revision'''

    log = repo.changelog
    n = 0

    if ui.verbose:
        ui.write("rev=%s limit=%s stop=%s\n" % (rev,limit,stop))

    # TODO: If no limit is given, ask after 100 or so whether to continue
    if limit is None or limit == '':
        limit = 100
    else:
        limit = int(limit)

    if not (stop is None or stop == ''):
        stop = repo.lookup(stop)
        if ui.verbose:
            ui.write("  stop = %s\n" % hex(stop))
    
    current = repo.lookup(rev)
    while n < limit or limit == 0:
        ctx = repo.changectx(current)
        parents = [ p for p in log.parents(current) if p != nullid ]
        header = short(current)
        if len(parents) != 1:
            header += " (%d parents)" % len(parents)
        desc = ctx.description().strip()
        desc = desc.replace("\n", " ")
        ui.write("%s: %s\n" % (header, desc))
        if len(parents) > 2:
            break

        if current == stop:
            break

        if len(parents) == 0:
            break

        current = parents[0]
        n += 1

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
    if ui.verbose:
        ui.write("fetched %s for bugs %s\n" % (conn.geturl(), ",".join(bugs)))
    try:
        buginfo = json.load(conn)
    except Exception, e:
        pass

    if buginfo.get('result', None) is None:
        if 'error' in buginfo:
            m = re.search(r'Bug #(\d+) does not exist', buginfo['error']['message'])
            if m:
                if ui.verbose:
                    ui.write("  dropping out nonexistent bug %s\n" % m.group(1))
                bugs.remove(m.group(1))
                return fetch_bugs(url, ui, bugs)

        ui.write("Failed to retrieve bugs\n")
        ui.write("buginfo: %r\n" % buginfo)
        return

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
        if ui.verbose:
            ui.write("bug %s: %s\n" % (b['id'], comp))
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

def qbackout(ui, repo, rev, **opts):
    """backout a change or set of changes

    qbackout creates a new patch or patches on top of any currently-applied
    patches. If the -s/--single option is set, then all backed-out changesets
    will be rolled up into a single backout changeset. Otherwise, there will
    be one backout changeset queued up for each backed-out changeset.
    """
    q = repo.mq
    if not opts.get('force'):
        ui.status('checking for uncommitted changes\n')
        cmdutil.bailifchanged(repo)

    rev = scmutil.revrange(repo, rev)
    if len(rev) == 0:
        raise util.Abort('at least one revision required')

    csets = map(lambda r: scmutil.revsingle(repo, r), rev)
    csets.sort(reverse=True, key=lambda cset: cset.rev())

    if opts.get('single') and opts.get('name') and len(rev) > 1:
        raise util.Abort('option "-n" not valid when backing out multiple changes')

    revert_opts = { 'date': None,
                    'all': True,
                    'no_backup': None,
                  }
    new_opts = opts.copy()
    mq.setupheaderopts(ui, new_opts)

    def bugs_suffix(bugs):
        if len(bugs) == 0:
            return ''
        elif len(bugs) == 1:
            return ' (bug ' + bugs.pop() + ')'
        else:
            return ' (' + ', '.join(map(lambda b: 'bug %s' % b, bugs)) + ')'

    allbugs = set()
    messages = []
    for cset in csets:
        bugs = set()
        m = bug_re.search(cset.description())
        if m:
            bugs.add(m.group(2))
        allbugs.update(bugs)
        shortnode = short(cset.node())
        ui.status('backing out %s\n' % shortnode)
        p1, p2 = repo.changelog.parents(cset.node())
        if p2 != nullid:
            raise util.Abort('cannot backout a merge changeset')
        revert_opts['rev'] = shortnode
        commands.revert(ui, repo, **revert_opts)
        msg = ('Backed out changeset %s' % shortnode) + bugs_suffix(bugs)
        messages.append(msg)
        if not opts.get('single'):
            new_opts['message'] = messages[-1]
            patchname = opts.get('name') or 'backout-%s' % shortnode
            mq.new(ui, repo, patchname, **new_opts)
            if ui.verbose:
                ui.write("queued up patch %s\n" % patchname)

    msg = ('Backed out %d changesets' % len(rev)) + bugs_suffix(allbugs) + '\n'
    messages.insert(0, msg)
    new_opts['message'] = "\n".join(messages)
    if opts.get('single'):
        patchname = opts.get('name') or 'backout-%d-changesets' % len(rev)
        mq.new(ui, repo, patchname, **new_opts)

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

# Monkeypatch qrefresh in mq command table
# Oddity: The default value of the parameter is moved to here because it
# contains a newline, which messes up the formatting of the help message
def qrefresh_wrapper(self, repo, *pats, **opts):
    mqmessage = opts.pop('mqmessage', '') or '%a: %p\n%s'
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

    mq.refresh(self, repo, *pats, **opts)

    if mqcommit and len(q.applied) > 0:
        patch = q.applied[-1].name
        if r is None:
            raise util.Abort("no patch repository found when using -Q option")
        mqmessage = mqmessage.replace("%p", patch)
        mqmessage = mqmessage.replace("%a", 'UPDATE')
        mqmessage = mqmessage.replace("%s", diffstat)
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qnew in mq command table
def qnew_wrapper(self, repo, patchfn, *pats, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    mq.new(self, repo, patchfn, *pats, **opts)

    if mqcommit and mqmessage:
        mqmessage = mqmessage.replace("%p", patchfn)
        mqmessage = mqmessage.replace("%a", 'NEW')
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qimport in mq command table
def qimport_wrapper(self, repo, *filename, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    mq.qimport(self, repo, *filename, **opts)

    if mqcommit and mqmessage:
        if len(filename) == 0:
            fname = q.full_series[0] # FIXME - can be multiple
        else:
            fname = filename[0] # FIXME - can be multiple
        mqmessage = mqmessage.replace("%p", fname)
        mqmessage = mqmessage.replace("%a", 'IMPORT')
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qrename in mq command table
def qrename_wrapper(self, repo, patch, name=None, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    mq.rename(self, repo, patch, name, **opts)

    if mqcommit and mqmessage:
        if not name:
            name = patch
            patch = q.lookup('qtip')
        mqmessage = mqmessage.replace("%p", patch)
        mqmessage = mqmessage.replace("%n", name)
        mqmessage = mqmessage.replace("%a", 'RENAME')
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qdelete in mq command table
def qdelete_wrapper(self, repo, *patches, **opts):
    '''This function takes a list of patches, which makes the message
    substitution rather weird. %a and %p will be replaced with the
    action ('DELETE') and patch name, as usual, but one line per patch
    will be generated. In addition the %m (multi?) replacement string,
    if given, will be replaced with a prefix message "DELETE (n)
    patches: patch1 patch2..." that is NOT repeated per patch. It
    probably would have been cleaner to give two formats, one for the
    header and one for the per-patch lines.'''

    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    if mqcommit and mqmessage:
        patchnames = [ q.lookup(p) for p in patches ]

    mq.delete(self, repo, *patches, **opts)

    if mqcommit and mqmessage:
        mqmessage = mqmessage.replace("%a", 'DELETE')
        if (len(patches) > 1) and (mqmessage.find("%m") != -1):
            rep_message = mqmessage.replace("%m", "")
            mqmessage = "DELETE %d patches: %s\n" % (len(patches), " ".join(patchnames))
            mqmessage += "\n".join([ rep_message.replace("%p", p) for p in patchnames ])
        else:
            mqmessage = mqmessage.replace("%m", "")
            mqmessage = "\n".join([ mqmessage.replace("%p", p) for p in patchnames ])
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qnew in mq command table
def qfinish_wrapper(self, repo, *revrange, **opts):
    mqmessage = opts.pop('mqmessage', None)
    mqcommit, q, r = mqcommit_info(self, repo, opts)

    mq.finish(self, repo, *revrange, **opts)

    if mqcommit and mqmessage:
        commands.commit(r.ui, r, message=mqmessage)

def wrap_mq_function(orig, wrapper, newparams):
    for key,info in mq.cmdtable.iteritems():
        if info[0] == orig:
            wrapper.__doc__ = info[0].__doc__
            mq.cmdtable[key] = (wrapper, info[1] + newparams, info[2])
            return

wrap_mq_function(mq.refresh,
                 qrefresh_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '', 'commit message for patch update')])

wrap_mq_function(mq.new,
                 qnew_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '%a: %p', 'commit message for patch creation')])

wrap_mq_function(mq.qimport,
                 qimport_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', 'IMPORT: %p', 'commit message for patch import')])

wrap_mq_function(mq.delete,
                 qdelete_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '%m%a: %p', 'commit message for patch deletion')])

wrap_mq_function(mq.rename,
                 qrename_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '%a: %p -> %n', 'commit message for patch rename')])

wrap_mq_function(mq.finish,
                 qfinish_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', 'FINISHED', 'commit message for patch finishing')])

cmdtable = {
    'qshow': (qshow,
              [('', 'stat', None, 'output diffstat-style summary of changes'),
               ],
              ('hg qshow [patch]')),

    'lineage':
        (lineage,
         [('r', 'rev', '.', 'revision to start at', 'REV'),
          ('l', 'limit', '', 'max revisions to display', 'LIMIT'),
          ('s', 'stop', '', 'stop at this revision', 'REV'),
          ],
         ('hg lineage -r REV [-l LIMIT] [-s REV]')),

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

    'qbackout':
        (qbackout,
         [('r', 'rev', [], _('revisions to backout')),
          ('n', 'name', '', _('name of patch file'), _('NAME')),
          ('s', 'single', None, _('fold all backed out changes into a single changeset')),
          ('f', 'force', None, _('skip check for outstanding uncommitted changes')),
          ('e', 'edit', None, _('edit commit messages')),
          ('m', 'message', '', _('use text as commit message'), _('TEXT')),
          ('U', 'currentuser', None, _('add "From: <current user>" to patch')),
          ('u', 'user', '',
           _('add "From: <USER>" to patch'), _('USER')),
          ('D', 'currentdate', None, _('add "Date: <current date>" to patch')),
          ('d', 'date', '',
           _('add "Date: <DATE>" to patch'), _('DATE')),
          ],
         ('hg qbackout -r REVS [-f] [-n NAME] [qnew options]')),
}
