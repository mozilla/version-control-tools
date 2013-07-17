'''backout a series of changesets

This is a port of mak's mercurial backout script from
https://wiki.mozilla.org/User:Mak77 to a mercurial extension.'''

testedwith = '2.5.2'

from mercurial import scmutil, commands, cmdutil, patch, mdiff, util
from mercurial.i18n import _
from mercurial.node import nullid, short
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

backout_re = re.compile(r'[bB]ack(?:ed)?(?: ?out) (?:(?:changeset|revision|rev) )?([a-fA-F0-9]{8,40})')
reapply_re = re.compile(r'Reapplied (?:(?:changeset|revision|rev) )?([a-fA-F0-9]{8,40})')

def qbackout(ui, repo, rev, **opts):
    """backout a change or set of changes

    qbackout creates a new patch or patches on top of any currently-applied
    patches. If the -s/--single option is set, then all backed-out changesets
    will be rolled up into a single backout changeset. Otherwise, there will
    be one backout changeset queued up for each backed-out changeset.

    The --apply option will reapply a patch instead of backing it out, which
    can be useful when you (or someone else) has backed your patch out and
    you want to try again.

    Normally, qbackout will error out if the patch (backout or application)
    fails to apply. The --broken option may be used to leave the patch in your
    queue so you can fix the conflicts manually.

    Examples:
      hg qbackout -r 20 -r 30    # backout revisions 20 and 30

      hg qbackout -r 20+30       # backout revisions 20 and 30

      hg qbackout -r 20+30:32    # backout revisions 20, 30, 31, and 32

      hg qbackout -r a3a81775    # the usual revision syntax is available

    See "hg help revisions" and "hg help revsets" for more about specifying
    revisions.
    """
    if not opts.get('force'):
        ui.status('checking for uncommitted changes\n')
        cmdutil.bailifchanged(repo)
    backout = not opts.get('apply')
    desc = { 'action': 'backout',
             'Actioned': 'Backed out',
             'actioning': 'backing out',
             'name': 'backout'
             }
    if not backout:
        desc = { 'action': 'apply',
                 'Actioned': 'Reapplied',
                 'actioning': 'Reapplying',
                 'name': 'patch'
                 }

    rev = scmutil.revrange(repo, rev)
    if len(rev) == 0:
        raise util.Abort('at least one revision required')

    csets = [ repo[r] for r in rev ]
    csets.sort(reverse=backout, key=lambda cset: cset.rev())

    if opts.get('single') and opts.get('name') and len(rev) > 1:
        raise util.Abort('option "-n" not valid when backing out multiple changes')

    new_opts = opts.copy()
    mq.setupheaderopts(ui, new_opts)

    def bugs_suffix(bugs):
        if len(bugs) == 0:
            return ''
        elif len(bugs) == 1:
            return ' (bug ' + list(bugs)[0] + ')'
        else:
            return ' (' + ', '.join(map(lambda b: 'bug %s' % b, bugs)) + ')'

    def parse_bugs(msg):
        bugs = set()
        m = bug_re.search(msg)
        if m:
            bugs.add(m.group(2))
        return bugs

    def apply_change(node, reverse):
        p1, p2 = repo.changelog.parents(node)
        if p2 != nullid:
            raise util.Abort('cannot %s a merge changeset' % desc['action'])

        opts = mdiff.defaultopts
        opts.git = True
        rpatch = StringIO.StringIO()
        orig, mod = (node, p1) if reverse else (p1, node)
        for chunk in patch.diff(repo, node1=orig, node2=mod, opts=opts):
            rpatch.write(chunk)
        rpatch.seek(0)

        saved_stdin = None
        try:
            save_fin = ui.fin
            ui.fin = rpatch
        except:
            # Old versions of hg did not use the ui.fin mechanism
            saved_stdin = sys.stdin
            sys.stdin = rpatch
        commands.import_(ui, repo, '-',
                         force=True,
                         no_commit=True,
                         strip=1,
                         base='')
        if saved_stdin is None:
            ui.fin = save_fin
        else:
            sys.stdin = saved_stdin

    allbugs = set()
    messages = []
    for cset in csets:
        # Hunt down original description if we might want to use it
        orig_desc = None
        orig_desc_cset = None
        orig_author = None
        r = cset
        while len(csets) == 1 or not opts.get('single'):
            ui.debug("Parsing message for %s\n" % short(r.node()))
            m = backout_re.match(r.description())
            if m:
                ui.debug("  looks like a backout of %s\n" % m.group(1))
            else:
                m = reapply_re.match(r.description())
                if m:
                    ui.debug("  looks like a reapply of %s\n" % m.group(1))
                else:
                    ui.debug("  looks like the original description\n")
                    orig_desc = r.description()
                    orig_desc_cset = r
                    orig_author = r.user()
                    break
            r = repo[m.group(1)]

        bugs = parse_bugs(cset.description())
        allbugs.update(bugs)
        node = cset.node()
        shortnode = short(node)
        ui.status('%s %s\n' % (desc['actioning'], shortnode))
        try:
            apply_change(node, backout)
        except:
            if not opts.get('broken'):
                raise
        msg = ('%s changeset %s' % (desc['Actioned'], shortnode)) + bugs_suffix(bugs)
        user = None

        if backout:
            # If backing out a backout, reuse the original commit message & author.
            if orig_desc_cset is not None and orig_desc_cset != cset:
                msg = orig_desc
                user = orig_author
        else:
            # If reapplying the original change, reuse the original commit message & author.
            if orig_desc_cset is not None and orig_desc_cset == cset:
                msg = orig_desc
                user = orig_author

        messages.append(msg)
        if not opts.get('single'):
            new_opts['message'] = messages[-1]
            patchname = opts.get('name') or '%s-%s' % (desc['name'], shortnode)
            # Override the user to that of the original patch author in the case of --apply
            if user is not None:
                new_opts['user'] = user
            mq.new(ui, repo, patchname, **new_opts)
            if ui.verbose:
                ui.write("queued up patch %s\n" % patchname)

    msg = ('%s %d changesets' % (desc['Actioned'], len(rev))) + bugs_suffix(allbugs) + '\n'
    messages.insert(0, msg)
    new_opts['message'] = "\n".join(messages)
    if opts.get('single'):
        patchname = opts.get('name') or '%s-%d-changesets' % (desc['name'], len(rev))
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
          ('', 'apply', False, _('re-apply a change instead of backing out')),
          ('', 'broken', None, _('backout even if patch does not fully apply')),
          ],
         ('hg qbackout -r REVS [-f] [-n NAME] [qnew options]')),
}

