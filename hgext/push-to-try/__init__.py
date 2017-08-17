# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from mercurial import (
    commands,
    context,
    cmdutil,
    registrar,
    util,
)
from mercurial.i18n import _

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

from mozhg.rewrite import preservefilectx

cmdtable = {}

# Mercurial 4.3 introduced registrar.command as a replacement for
# cmdutil.command.
if util.safehasattr(registrar, 'command'):
    command = registrar.command(cmdtable)
else:
    command = cmdutil.command(cmdtable)

testedwith = '3.9 4.0 4.1 4.2'

@command('push-to-try', [
    ('m', 'message', '', 'commit message to use', 'MESSAGE'),
    ('s', 'server', 'ssh://hg.mozilla.org/try', 'push destination', 'URL'),
], '-m MESSAGE -s URL')
def push_to_try(ui, repo, server, message=None):

    nodate = ui.configbool('push-to-try', 'nodate')

    if not message:
        ui.status("STOP! A commit message is required.\n")
        return

    cctx = context.workingctx(repo)
    if 'try_task_config.json' not in cctx and 'try:' not in message:
        ui.status("STOP! Either try_task_config.json must be added or the commit "
                  "message must contain try syntax.\n")
        return

    # Invent a temporary commit with our message.
    ui.status("Creating temporary commit for remote...\n")
    status = repo.status()
    if status.modified + status.added + status.removed:
        # TODO: Achieve this by re-using the status call above to avoid the
        # cost of running it twice.
        commands.status(ui, repo)

    preserve_ctx = preservefilectx(cctx)
    def mk_memfilectx(repo, memctx, path):
        if path not in status.removed:
            return preserve_ctx(repo, memctx, path)
        return None

    mctx = context.memctx(repo,
                          repo.dirstate.parents(),
                          message,
                          cctx.files(),
                          mk_memfilectx,
                          date="0 0" if nodate else None)

    # These messages are expected when we abort our transaction, but aren't
    # helpful to a user and may be misleading so we surpress them here.
    filtered_phrases = {_("transaction abort!\n"),
                        _("rollback completed\n")}
    def filtered_warn(*msgs, **opts):
        if msgs:
            filtered = [m for m in msgs if m not in filtered_phrases]
        if filtered:
            ui.warn(*filtered, **opts)

    lock = tr = None
    try:
        lock = repo.lock()
        tr = repo.transaction('push-to-try', report=filtered_warn)
        m = mctx.commit()
        # Push to try.
        commands.push(ui, repo, server, force=True, rev=[repo[m].rev()])
        ui.status('push complete\n')
        # And rollback to the previous state.
        tr.abort()
    finally:
        if tr:
            tr.release()
        if lock:
            lock.release()
        ui.status("temporary commit removed, repository restored\n")
