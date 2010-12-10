'''tweak the mq extension -- add some convenience commands and parameters

Note that many if not all of these changes should really be made to the
upstream project. I just haven't gotten around to it.

Commands added:
  qshow - Display a single patch (similar to 'export')
  qexport - Write all patches to an output directory, with minor renaming
  qtouched - See what patches modify which files

The following commands are modified to add options that autocommit any
changes made to your patch queue to the queue repository
(a la hg commit --mq):
  qrefresh
  qnew
  qrename
  qdelete
The expected usage is to add the -Q option to all relevant commands in your
~/.hgrc so that all changes are autocommitted:

  [defaults]
  qnew = -Q
  qrefresh = -Q
  qrename = -Q
  qdelete = -Q

Commands not related to mq:
  lineage - Dump out the revision history leading up to a particular revision
'''

# TODO:
# [ ] Make 'show' dispatch to export?diff? for eg --stat
#     - Hmm. No. export is all about generating a patch from adjacent revisions
#       We already have a patch.
# [ ] Make qexport rediff with new options (eg -U 8)
#     - For this, dispatching to export would make a lot of sense, but I guess
#       I'd have to restrict it to applied patches then (b/c I don't really
#       want to construct the revs to feed to export by applying patches...)

import os
from subprocess import call, check_call
import errno
from mercurial.node import hex, nullrev, nullid, short
from mercurial import commands, util, cmdutil, mdiff
from mercurial.patch import diffstatdata
from hgext import mq
import StringIO

def qshow(ui, repo, patch=None, **opts):
    '''display a patch

    If no patch is given, the top of the applied stack is shown.'''
    q = repo.mq

    if patch is None:
        try:
            patch = q.applied[-1].name
        except:
            ui.write("No patches in series\n");
            return

    # Try to interpret the patch as an index into the full stack
    try:
        idx = int(patch)
        patch = q.series[idx]
    except:
        pass

    # This should probably dispatch to export, so that all of its
    # options could be used.
    if opts['stat']:
        check_call(["diffstat", "-p1", q.join(patch)])
    else:
        try:
            ui.write(file(q.join(patch)).read())
        except:
            ui.write("Invalid patch name '%s'\n" % (patch,))

# TODO: I would really like to be able to export with a different
# amount of context than is stored in the patch. (I'd like to store
# less context so that the patches are more likely to apply, but
# export with more context to make reviews easier)
#
# Without that feature, I'm not sure this command is useful. Your
# patches are already stored in a directory.
def qexport(ui, repo, outdir, **opts):
    '''Save all applied patches into a directory'''

    try:
        os.mkdir(outdir)
    except OSError, inst:
        if inst.errno != errno.EEXIST:
            raise

    suffix = ''
    if opts['extension']:
        suffix += '.' + opts['extension']
    if opts['patch']:
        suffix += '.patch'

    q = repo.mq

    n = 0
    numlen = len(str(len(q.applied)))

    for p in q.applied:
        stem = p.name + suffix
        if opts['numbered']:
            stem = (('%0' + str(numlen) + 'd-') % n) + stem
        n += 1
        filename = os.path.join(outdir, stem)

        # This should really call p.export(...) instead of writing the
        # file directly...
        open(filename, 'w').write(file(q.join(p.name)).read())
        if ui.verbose:
            ui.write("Wrote %s\n" % filename)

def lineage(ui, repo, rev='.', limit=None, stop=None, **opts):
    '''Show ancestors of a revision'''

    log = repo.changelog
    n = 0

    print("rev=%s limit=%s stop=%s\n" % (rev,limit,stop))

    # TODO: If no limit is given, ask after 100 or so whether to continue
    if limit is None or limit == '':
        limit = 100
    else:
        limit = int(limit)

    if not (stop is None or stop == ''):
        print("stop = %r\n" % (stop,))
        stop = repo.lookup(stop)
    
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

        current = parents[0]
        n += 1
 
def touched(ui, repo, sourcefile=None, **opts):
    '''Show what files are touched by what patches

    If no file is given, print out a series of lines containing a
    patch and a file changed by that patch, for all files changed by
    all patches. This is mainly intended for easy grepping.

    If a file is given, print out the list of patches that touch that file.'''

    q = repo.mq

    if opts['applied']:
        patches = [ p.name for p in q.applied ]
    else:
        patches = q.series

    for patch in [ q.lookup(p) for p in patches ]:
        lines = file(q.join(patch)).read().splitlines()
        for filename, adds, removes, isbinary in diffstatdata(lines):
            if sourcefile is None:
                ui.write(patch + "\t" + filename + "\n")
            elif sourcefile == filename:
                ui.write(patch + "\n")

# Monkeypatch qrefresh in mq command table
def qrefresh_wrapper(self, repo, *pats, **opts):
    mqcommit = opts.pop('mqcommit', None)
    mqmessage = opts.pop('mqmessage', None)

    diffstat = ""
    if mqcommit:
        q = repo.mq
        r = q.qrepo()
        if mqmessage.find("%s") != -1:
            buffer = StringIO.StringIO()
            m = cmdutil.match(repo, None, {})
            diffopts = mdiff.diffopts()
            cmdutil.diffordiffstat(self, repo, diffopts,
                                   repo.dirstate.parents()[0], None, m,
                                   stat=True, fp = buffer)
            diffstat = buffer.getvalue()
            buffer.close()

    mq.refresh(self, repo, *pats, **opts)

    if mqcommit:
        patch = q.applied[-1].name
        if r is None:
            raise util.Abort("no patch repository found when using -Q option")
        mqmessage = mqmessage.replace("%p", patch)
        mqmessage = mqmessage.replace("%a", 'UPDATE')
        mqmessage = mqmessage.replace("%s", diffstat)
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qnew in mq command table
def qnew_wrapper(self, repo, patchfn, *pats, **opts):
    mqcommit = opts.pop('mqcommit', None)
    mqmessage = opts.pop('mqmessage', None)

    mq.new(self, repo, patchfn, *pats, **opts)

    if mqcommit:
        q = repo.mq
        r = q.qrepo()
        if r is None:
            raise util.Abort("no patch repository found when using -Q option")
        mqmessage = mqmessage.replace("%p", patchfn)
        mqmessage = mqmessage.replace("%a", 'NEW')
        commands.commit(r.ui, r, message=mqmessage)

# Monkeypatch qrename in mq command table
def qrename_wrapper(self, repo, patch, name=None, **opts):
    mqcommit = opts.pop('mqcommit', None)
    mqmessage = opts.pop('mqmessage', None)

    mq.rename(self, repo, patch, name, **opts)

    if mqcommit:
        q = repo.mq
        if not name:
            name = patch
            patch = q.lookup('qtip')
        r = q.qrepo()
        if r is None:
            raise util.Abort("no patch repository found when using -Q option")
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

    mqcommit = opts.pop('mqcommit', None)
    mqmessage = opts.pop('mqmessage', None)

    if mqcommit:
        q = repo.mq
        r = q.qrepo()
        if r is None:
            raise util.Abort("no patch repository found when using -Q option")
        patchnames = [ q.lookup(p) for p in patches ]

    mq.delete(self, repo, *patches, **opts)

    if mqcommit:
        mqmessage = mqmessage.replace("%a", 'DELETE')
        if (len(patches) > 1) and (mqmessage.find("%m") != -1):
            rep_message = mqmessage.replace("%m", "")
            mqmessage = "DELETE %d patches: %s\n" % (len(patches), " ".join(patchnames))
            mqmessage += "\n".join([ rep_message.replace("%p", p) for p in patchnames ])
        else:
            mqmessage = mqmessage.replace("%m", "")
            mqmessage = "\n".join([ mqmessage.replace("%p", p) for p in patchnames ])
        commands.commit(r.ui, r, message=mqmessage)

def wrap_mq_function(orig, wrapper, newparams):
    for key,info in mq.cmdtable.iteritems():
        if info[0] == orig:
            mq.cmdtable[key] = (wrapper, info[1] + newparams, info[2])
            return

wrap_mq_function(mq.refresh,
                 qrefresh_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '%a: %p\n%s', 'commit message for patch update')])

wrap_mq_function(mq.new,
                 qnew_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '%a: %p', 'commit message for patch creation')])

wrap_mq_function(mq.delete,
                 qdelete_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '%m%a: %p', 'commit message for patch deletion')])

wrap_mq_function(mq.rename,
                 qrename_wrapper,
                 [('Q', 'mqcommit', None, 'commit change to patch queue'),
                  ('M', 'mqmessage', '%a: %p -> %n', 'commit message for patch rename')])

cmdtable = {
    'qshow': (qshow,
              [('', 'stat', None, 'output diffstat-style summary of changes'),
               ],
              ('hg qshow [patch]')),

    'qexport':
        (qexport,
         [('p', 'patch', None, 'add .patch suffix to exported patches'),
          ('e', 'extension', '', 'append .EXTENSION to exported patches'),
          ('n', 'numbered', None, 'prefix patch names with order numbers'),
          ('d', 'outdir', '/tmp/patches', 'directory to write patches into'),
          ],
         ('hg qexport [-p] [-e EXTENSION] [-n]')),

    'lineage':
        (lineage,
         [('r', 'rev', '', 'Revision to start at', 'REV'),
          ('l', 'limit', '', 'Max revisions to display', 'LIMIT'),
          ('s', 'stop', '', 'Stop at this revision', 'REV'),
          ],
         ('hg lineage -r REV [-l LIMIT] [-s REV]')),

    'qtouched':
        (touched,
         [('a', 'applied', None, 'Only consider applied patches')
          ],
         ('hg touched [-p PATCH] [FILE]')),
}
