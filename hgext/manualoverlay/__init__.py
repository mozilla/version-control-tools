# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os
import re
import urllib

from mercurial.i18n import _
from mercurial import (
    commands,
    demandimport,
    encoding,
    error,
    extensions,
    pycompat,
    registrar,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(OUR_DIR, '..', 'bootstrap.py')) as f:
    exec(f.read())

# requests doesn't like lazy importing
with demandimport.deactivated():
    import requests  # noqa


testedwith = b'4.4 4.5 4.6 4.7 4.8 4.9 5.0'

cmdtable = {}

command = registrar.command(cmdtable)

REVISION_KEY = b'subtree_revision'
SOURCE_KEY = b'subtree_source'
LINEAR_REPO_URL = b'https://hg.mozilla.org/projects/converted-servo-linear'
GITHUB_PR_URL = re.compile(
    br'https://github\.com/servo/servo/pull/(?P<pr>[1-9][0-9]*)/?')
COMMIT_MSG_PR = re.compile(br'servo: Merge #(?P<pr>[1-9][0-9]*) - .*')


def commitcommand(orig, ui, repo, *args, **kwargs):
    pr_url = kwargs.get('manualservosync')
    if not pr_url:
        return orig(ui, repo, *args, **kwargs)

    m = GITHUB_PR_URL.match(pr_url)
    if m is None:
        raise error.Abort(
            _(b'--manualservosync was not a proper github pull request url'),
            hint=_(b'url must be to a servo/servo pull request of the form '
                   b'https://github.com/servo/servo/pull/<pr-number>'))

    pr = m.group('pr')

    revset = urllib.quote(b'keyword("servo: Merge #%s")' % pr)
    url = b'%s/json-log?rev=%s' % (LINEAR_REPO_URL, revset)
    r = requests.get(url)
    commits = r.json()[b'entries']

    if not commits:
        raise error.Abort(
            _(b'could not find linearized commit corresponding to %s' % pr_url),
            hint=_(b'If this pull requests has recently been merged it '
                   b'may not be linearized yet, please try again soon'))

    repo.manualsync_commit = {
        b'desc': encoding.tolocal(commits[0][b'desc'].encode('utf-8')),
        b'node': encoding.tolocal(commits[0][b'node'].encode('utf-8')),
        b'user': encoding.tolocal(commits[0][b'user'].encode('utf-8')),
    }
    repo.manualsync_pr = pr
    repo.manualsync = True
    return orig(ui, repo, *args, **kwargs)


def reposetup(ui, repo):
    if not repo.local():
        return

    class servosyncrepo(repo.__class__):
        def commit(self, *args, **kwargs):
            if not self.manualsync:
                return super(servosyncrepo, self).commit(*args, **kwargs)

            kwargs = pycompat.byteskwargs(kwargs)

            # Override some of the commit meta data.
            msg = self.manualsync_commit[b'desc']
            user = self.manualsync_commit[b'user']

            # This method has many keyword arguments that mercurial
            # ocassionally passes positionally, meanig they end up
            # in *args, instead of **kwargs. This can be problematic as
            # naively modifying the value in **kwargs will result in
            # the argument being passed twice, which is an error.
            # Protect against this by stripping the values out of
            # *args and **kwargs, passing them positionally ourselves.
            for key in (b'text', b'user'):
                if args:
                    args = args[1:]

                if key in kwargs:
                    del kwargs[key]

            kwargs[b'extra'] = kwargs[b'extra'] if b'extra' in kwargs else {}
            kwargs[b'extra'][SOURCE_KEY] = encoding.tolocal(LINEAR_REPO_URL)
            kwargs[b'extra'][REVISION_KEY] = self.manualsync_commit[b'node']

            # TODO: Verify that the file changes being committed are only
            # under the servo/ directory.
            ret = super(servosyncrepo, self).commit(
                msg, user, *args, **pycompat.strkwargs(kwargs))

            ctx = repo[ret]

            if any(not f.startswith(b'servo/') for f in ctx.files()):
                self.ui.warn(
                    _(b'warning: this commit touches files outside the servo '
                      b'directory and would be rejected by the server\n'))

            return ctx

    repo.__class__ = servosyncrepo
    repo.manualsync = False


def extsetup(ui):
    entry = extensions.wrapcommand(commands.table, b'commit', commitcommand)
    options = entry[1]
    options.append(
        (b'', b'manualservosync', b'',
         b'manually overlay and sync a servo pull request', _(b"GH_PR_URL")))
