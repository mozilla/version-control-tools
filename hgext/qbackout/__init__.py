'''backout a series of changesets

This is a port of mak's mercurial backout script from
https://wiki.mozilla.org/User:Mak77 to a mercurial extension.'''

import gc
import os
import re
import StringIO

from mercurial.i18n import _
from mercurial.node import nullid, short
from mercurial import (
    cmdutil,
    commands,
    mdiff,
    patch,
    registrar,
    scmutil,
    util,
)
from hgext import mq


OUR_DIR = os.path.dirname(__file__)
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozautomation.commitparser import BUG_CONSERVATIVE_RE
# mercurial version portability
import sys
if not getattr(cmdutil, 'bailifchanged', None):
    cmdutil.bailifchanged = cmdutil.bail_if_changed
if 'mercurial.scmutil' not in sys.modules:
    import mercurial.cmdutil as scmutil

testedwith = '3.9 4.0 4.1 4.2'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20qbackout'

cmdtable = {}

# Mercurial 4.3 introduced registrar.command as a replacement for
# cmdutil.command.
if util.safehasattr(registrar, 'command'):
    command = registrar.command(cmdtable)
else:
    command = cmdutil.command(cmdtable)

backout_re = re.compile(r'[bB]ack(?:ed)?(?: ?out) (?:(?:changeset|revision|rev) )?([a-fA-F0-9]{8,40})')
reapply_re = re.compile(r'Reapplied (?:(?:changeset|revision|rev) )?([a-fA-F0-9]{8,40})')


@command('qbackout', [
    ('r', 'rev', [], _('revisions to backout')),
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
    ('', 'nopush', False, _('do not push patches (useful when they do not apply properly)'))],
    _('hg qbackout -r REVS [-f] [-n NAME] [qnew options]'))
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
    fails to apply. The --nopush option may be used to leave the patch in your
    queue without pushing it so you can fix the conflicts manually.

    Examples:
      hg qbackout -r 20 -r 30    # backout revisions 20 and 30

      hg qbackout -r 20+30       # backout revisions 20 and 30

      hg qbackout -r 20+30:32    # backout revisions 20, 30, 31, and 32

      hg qbackout -r a3a81775    # the usual revision syntax is available

    See "hg help revisions" and "hg help revsets" for more about specifying
    revisions.
    """
    reverse_order = not opts.get('apply')
    if opts.get('nopush'):
        reverse_order = not reverse_order

    if opts.get('nopush') and opts.get('single'):
        ui.fatal("--single not supported with --nopush")

    new_opts = opts.copy()
    mq.setupheaderopts(ui, new_opts)

    name_used = [False]

    def compute_patch_name(action, force_name, node=None, revisions=None):
        if force_name:
            if name_used[0]:
                raise util.Abort('option "-n" not valid when backing out multiple changes')
            name_used[0] = True
            return force_name
        else:
            if node:
                return '%s-%s' % (action, short(node))
            else:
                return '%s-%d-changesets' % (action, len(revisions))

    def handle_change(desc, node, qimport=False):
        if qimport:
            name = compute_patch_name(desc['name'], opts.get('name'), node=node)
            mq.qimport(ui, repo, '-', name=name, rev=[], git=True)
        else:
            commands.import_(ui, repo, '-',
                             force=True,
                             no_commit=True,
                             strip=1,
                             base='',
                             prefix='',
                             obsolete=[])

    def commit_change(ui, repo, action, force_name=None, node=None, revisions=None, **opts):
        patchname = compute_patch_name(action, force_name, node=node, revisions=revisions)
        mq.new(ui, repo, patchname, **opts)
        if ui.verbose:
            ui.write("queued up patch %s\n" % patchname)

    do_backout(ui, repo, rev, handle_change, commit_change,
               reverse_order=reverse_order,
               **opts)


def do_backout(ui, repo, rev, handle_change, commit_change, use_mq=False, reverse_order=False, **opts):
    if not opts.get('force'):
        ui.status('checking for uncommitted changes\n')
        cmdutil.bailifchanged(repo)
    backout = not opts.get('apply')
    desc = {'action': 'backout',
            'Actioned': 'Backed out',
            'actioning': 'backing out',
            'name': 'backout'
            }
    if not backout:
        desc = {'action': 'apply',
                'Actioned': 'Reapplied',
                'actioning': 'Reapplying',
                'name': 'patch'
                }

    rev = scmutil.revrange(repo, rev)
    if len(rev) == 0:
        raise util.Abort('at least one revision required')

    csets = [repo[r] for r in rev]
    csets.sort(reverse=reverse_order, key=lambda cset: cset.rev())

    new_opts = opts.copy()

    def bugs_suffix(bugs):
        if len(bugs) == 0:
            return ''
        elif len(bugs) == 1:
            return ' (bug ' + list(bugs)[0] + ')'
        else:
            return ' (' + ', '.join(map(lambda b: 'bug %s' % b, bugs)) + ')'

    def parse_bugs(msg):
        bugs = set()
        m = BUG_CONSERVATIVE_RE.search(msg)
        if m:
            bugs.add(m.group(2))
        return bugs

    def apply_change(node, reverse, push_patch=True, name=None):
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

        handle_change(desc, node, qimport=(use_mq and new_opts.get('nopush')))

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

        apply_change(node, backout, push_patch=(not opts.get('nopush')))

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
        if not opts.get('single') and not opts.get('nopush'):
            new_opts['message'] = messages[-1]
            # Override the user to that of the original patch author in the case of --apply
            if user is not None:
                new_opts['user'] = user
            commit_change(ui, repo, desc['name'], node=node, force_name=opts.get('name'), **new_opts)

        # Iterations of this loop appear to leak memory for unknown reasons.
        # Work around it by forcing a gc.
        gc.collect()

    msg = ('%s %d changesets' % (desc['Actioned'], len(rev))) + bugs_suffix(allbugs) + '\n'
    messages.insert(0, msg)
    new_opts['message'] = "\n".join(messages)
    if opts.get('single'):
        commit_change(ui, repo, desc['name'], revisions=rev, force_name=opts.get('name'), **new_opts)


@command('oops', [
    ('r', 'rev', [], _('revisions to backout')),
    ('s', 'single', None, _('fold all backed out changes into a single changeset')),
    ('f', 'force', None, _('skip check for outstanding uncommitted changes')),
    ('e', 'edit', None, _('edit commit messages')),
    ('m', 'message', '', _('use text as commit message'), _('TEXT')),
    ('U', 'currentuser', None, _('add "From: <current user>" to patch')),
    ('u', 'user', '',
     _('add "From: <USER>" to patch'), _('USER')),
    ('D', 'currentdate', None, _('add "Date: <current date>" to patch')),
    ('d', 'date', '',
     _('add "Date: <DATE>" to patch'), _('DATE'))],
    _('hg oops -r REVS [-f] [commit options]'))
def oops(ui, repo, rev, **opts):
    """backout a change or set of changes

    oops commits a changeset or set of changesets by undoing existing changesets.
    If the -s/--single option is set, then all backed-out changesets
    will be rolled up into a single backout changeset. Otherwise, there will
    be one changeset queued up for each backed-out changeset.

    Note that if you want to reapply a previously backed out patch, use
    hg graft -f.

    Examples:
      hg oops -r 20 -r 30    # backout revisions 20 and 30

      hg oops -r 20+30       # backout revisions 20 and 30

      hg oops -r 20+30:32    # backout revisions 20, 30, 31, and 32

      hg oops -r a3a81775    # the usual revision syntax is available

    See "hg help revisions" and "hg help revsets" for more about specifying
    revisions.
    """
    def handle_change(desc, node, **kwargs):
        commands.import_(ui, repo, '-',
                         force=True,
                         no_commit=True,
                         strip=1,
                         base='',
                         prefix='',
                         obsolete=[])

    def commit_change(ui, repo, action, force_name=None, node=None, revisions=None, **opts):
        commands.commit(ui, repo, **opts)

    do_backout(ui, repo, rev,
               handle_change, commit_change,
               use_mq=True, reverse_order=(not opts.get('apply')),
               **opts)
