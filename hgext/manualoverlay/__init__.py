# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

import os
import re
import urllib

from mercurial.i18n import _
from mercurial import (
    cmdutil,
    commands,
    demandimport,
    encoding,
    error,
    extensions,
    registrar,
    util,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

# requests doesn't like lazy importing
with demandimport.deactivated():
    import requests  # noqa


testedwith = '4.3 4.4 4.5 4.6'

cmdtable = {}

# Mercurial 4.3 introduced registrar.command as a replacement for
# cmdutil.command.
if util.safehasattr(registrar, 'command'):
    command = registrar.command(cmdtable)
else:
    command = cmdutil.command(cmdtable)

REVISION_KEY = 'subtree_revision'
SOURCE_KEY = 'subtree_source'
LINEAR_REPO_URL = 'https://hg.mozilla.org/projects/converted-servo-linear'
GITHUB_PR_URL = re.compile(
    r'https://github\.com/servo/servo/pull/(?P<pr>[1-9][0-9]*)/?')
COMMIT_MSG_PR = re.compile(r'servo: Merge #(?P<pr>[1-9][0-9]*) - .*')


def commitcommand(orig, ui, repo, *args, **kwargs):
    pr_url = kwargs.get('manualservosync')
    if not pr_url:
        return orig(ui, repo, *args, **kwargs)

    m = GITHUB_PR_URL.match(pr_url)
    if m is None:
        raise error.Abort(
            _('--manualservosync was not a proper github pull request url'),
            hint=_('url must be to a servo/servo pull request of the form '
                   'https://github.com/servo/servo/pull/<pr-number>'))

    pr = m.group('pr')

    revset = urllib.quote('keyword("servo: Merge #%s")' % pr)
    url = '%s/json-log?rev=%s' % (LINEAR_REPO_URL, revset)
    r = requests.get(url)
    commits = r.json()['entries']

    if not commits:
        raise error.Abort(
            _('could not find linearized commit corresponding to %s' % pr_url),
            hint=_('If this pull requests has recently been merged it '
                   'may not be linearized yet, please try again soon'))

    repo.manualsync_commit = {
        'desc': encoding.tolocal(commits[0]['desc'].encode('utf-8')),
        'node': encoding.tolocal(commits[0]['node'].encode('utf-8')),
        'user': encoding.tolocal(commits[0]['user'].encode('utf-8')),
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

            # Override some of the commit meta data.
            msg = self.manualsync_commit['desc']
            user = self.manualsync_commit['user']

            # This method has many keyword arguments that mercurial
            # ocassionally passes positionally, meanig they end up
            # in *args, instead of **kwargs. This can be problematic as
            # naively modifying the value in **kwargs will result in
            # the argument being passed twice, which is an error.
            # Protect against this by stripping the values out of
            # *args and **kwargs, passing them positionally ourselves.
            for key in ('text', 'user'):
                if args:
                    args = args[1:]

                if key in kwargs:
                    del kwargs[key]

            kwargs['extra'] = kwargs['extra'] if 'extra' in kwargs else {}
            kwargs['extra'][SOURCE_KEY] = encoding.tolocal(LINEAR_REPO_URL)
            kwargs['extra'][REVISION_KEY] = self.manualsync_commit['node']

            # TODO: Verify that the file changes being committed are only
            # under the servo/ directory.
            ret = super(servosyncrepo, self).commit(
                msg, user, *args, **kwargs)

            ctx = repo[ret]

            if any(not f.startswith('servo/') for f in ctx.files()):
                self.ui.warn(
                    _('warning: this commit touches files outside the servo '
                      'directory and would be rejected by the server\n'))

            return ctx

    repo.__class__ = servosyncrepo
    repo.manualsync = False


def extsetup(ui):
    entry = extensions.wrapcommand(commands.table, 'commit', commitcommand)
    options = entry[1]
    options.append(
        ('', 'manualservosync', '',
         'manually overlay and sync a servo pull request', _("GH_PR_URL")))
