# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import json
from mercurial import (
    commands,
    context,
    registrar,
)
from mercurial.i18n import _

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

from mozhg.rewrite import preservefilectx

cmdtable = {}

command = registrar.command(cmdtable)

configtable = {}
configitem = registrar.configitem(configtable)

configitem('push-to-try', 'nodate',
           default=False)

testedwith = '4.6 4.7 4.8 4.9 5.0'
minimumhgversion = '4.6'

@command('push-to-try', [
    ('m', 'message', '', 'commit message to use', 'MESSAGE'),
    ('s', 'server', '', 'push destination', 'URL'),
], '-m MESSAGE -s URL')
def push_to_try(ui, repo, server, message=None):

    nodate = ui.configbool('push-to-try', 'nodate')

    if not server:
        if 'try' in ui.paths:
            server = 'try'
        else:
            server = 'ssh://hg.mozilla.org/try'

    if not message:
        ui.status("STOP! A commit message is required.\n")
        return

    cctx = context.workingctx(repo)
    if 'try_task_config.json' not in cctx and 'try:' not in message:
        ui.status("STOP! Either try_task_config.json must be added or the commit "
                  "message must contain try syntax.\n")
        return

    if 'try_task_config.json' in cctx:
        data = repo.wvfs.tryread('try_task_config.json')
        try:
            # data could be an empty string if tryread failed, which will
            # produce a ValueError here.
            data = json.loads(data)
        except ValueError as e:
            ui.status("Error reading try_task_config.json: %s\n" % e.message)
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
