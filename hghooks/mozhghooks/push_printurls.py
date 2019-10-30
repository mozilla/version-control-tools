#!/usr/bin/env python

from mozhg.util import (
    identify_repo,
)


def hook(ui, repo, node, hooktype, source=None, **kwargs):
    if source in (b'pull', b'strip'):
        return 0

    info = identify_repo(repo)
    if not info[b'hosted']:
        return 0

    # All changesets from node to "tip" inclusive are part of this push.
    rev = repo[node].rev()
    tipctx = repo[b'tip']
    tip = tipctx.rev()
    tip_node = tipctx.hex()

    num_changes = tip + 1 - rev
    url = b'https://hg.mozilla.org/%s/' % info[b'path']

    if num_changes <= 10:
        plural = b's' if num_changes > 1 else b''
        ui.write(b'\nView your change%s here:\n' % plural)

        for i in xrange(rev, tip + 1):
            node = repo[i].hex()
            ui.write(b'  %srev/%s\n' % (url, node))
    else:
        ui.write(b'\nView the pushlog for these changes here:\n')
        ui.write(b'  %spushloghtml?changeset=%s\n' % (url, tip_node))

    # For repositories that report CI results to Treeherder, also output a
    # Treeherder url.
    treeherder_repo = ui.config(b'mozilla', b'treeherder_repo')
    if treeherder_repo:
        treeherder_base_url = b'https://treeherder.mozilla.org'
        ui.write(b'\nFollow the progress of your build on Treeherder:\n')
        ui.write(b'  %s/#/jobs?repo=%s&revision=%s\n' % (treeherder_base_url,
                                                        treeherder_repo,
                                                        tip_node))
        # if specifying a try build and talos jobs are enabled, suggest that
        # user use compareperf
        if treeherder_repo == b'try':
            msg = repo[b'tip'].description()
            if ((b' -t ' in msg or b' --talos ' in msg) and b'-t none' not in msg
                and b'--talos none' not in msg):
                ui.write(b'\nIt looks like this try push has talos jobs. Compare '
                       b'performance against a baseline revision:\n')
                ui.write(b'  %s/perf.html#/comparechooser'
                         b'?newProject=try&newRevision=%s\n' % (
                             treeherder_base_url, tip_node))
    return 0
