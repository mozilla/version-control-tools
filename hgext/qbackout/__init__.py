'''backout a series of changesets

This is a port of mak's mercurial backout script from
https://wiki.mozilla.org/User:Mak77 to a mercurial extension.'''

import mercurial
from mercurial import scmutil, commands, cmdutil, patch
from mercurial.i18n import _
from mercurial.node import hex, nullid, short
from hgext import mq

import StringIO
import re

# mercurial version portability
import sys
if not getattr(cmdutil, 'bailifchanged', None):
    cmdutil.bailifchanged = cmdutil.bail_if_changed
if 'mercurial.scmutil' not in sys.modules:
    import mercurial.cmdutil as scmutil

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

def qbackout(ui, repo, rev, **opts):
    """backout a change or set of changes

    qbackout creates a new patch or patches on top of any currently-applied
    patches. If the -s/--single option is set, then all backed-out changesets
    will be rolled up into a single backout changeset. Otherwise, there will
    be one backout changeset queued up for each backed-out changeset.

    Examples:
      hg qbackout -r 20 -r 30    # backout revisions 20 and 30

      hg qbackout -r 20+30       # backout revisions 20 and 30

      hg qbackout -r 20+30:32    # backout revisions 20, 30, 31, and 32

      hg qbackout -r a3a81775    # the usual revision syntax is available

    See "hg help revisions" and "hg help revsets" for more about specifying
    revisions.
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

    def parse_bugs(msg):
        bugs = set()
        m = bug_re.search(msg)
        if m:
            bugs.add(m.group(2))
        return bugs

    def apply_reverse_change(node):
        p1, p2 = repo.changelog.parents(node)
        if p2 != nullid:
            raise util.Abort('cannot backout a merge changeset')

        rpatch = StringIO.StringIO()
        for chunk in patch.diff(repo, node1=node, node2=p1):
            rpatch.write(chunk)
        rpatch.seek(0)
        
        save_fin = ui.fin
        ui.fin = rpatch
        commands.import_(ui, repo, '-',
                         force=True,
                         no_commit=True,
                         strip=1,
                         base='')
        ui.fin = save_fin

    allbugs = set()
    messages = []
    for cset in csets:
        bugs = parse_bugs(cset.description())
        allbugs.update(bugs)
        node = cset.node()
        shortnode = short(node)
        ui.status('backing out %s\n' % shortnode)
        apply_reverse_change(node)
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


cmdtable = {
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

