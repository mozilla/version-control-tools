# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension to run hooks on repositories."""

from __future__ import absolute_import

from mozhg.util import (
    identify_repo,
)

import mozhghooks.checks as checksmod


testedwith = '4.2 4.3'
minimumhgversion = '4.2'
buglink = 'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org'


def get_checks(ui, repo, info, classes):
    """Loads checks from classes.

    Returns a list of check instances that are active for the given repo.
    """
    checks = []

    for cls in classes:
        check = cls(ui, repo, info)
        name = check.name

        force_enable = False
        force_disable = False
        override = ui.config('mozilla', 'check.%s' % name)
        if override in ('enable', 'true'):
            force_enable = True
        elif override in ('disable', 'false'):
            force_disable = True

        enabled = check.relevant()
        if not isinstance(enabled, bool):
            raise Exception('relevant() must return a bool; got %s' % enabled)

        if enabled and force_disable:
            ui.warn('(%s check disabled per config override)\n' %
                    name)
            continue
        elif not enabled and force_enable:
            ui.warn('(%s check enabled per config override)\n' %
                    name)
            enabled = True

        if enabled:
            checks.append(check)

    return checks


def pretxnchangegroup(ui, repo, node, source=None, **kwargs):
    # TODO come up with a mechanism for automatically discovering checks
    # so we don't have to enumerate them all.
    from mozhghooks.check import (
        prevent_symlinks,
        single_root,
        try_task_config_file,
    )

    CHECKS = (
        prevent_symlinks.PreventSymlinksCheck,
        single_root.SingleRootCheck,
        try_task_config_file.TryConfigCheck,
    )

    # Never apply hooks at pull time or when re-applying from strips.
    if source in ('pull', 'strip'):
        return 0

    info = identify_repo(repo)

    # Don't apply to non-hosted repos.
    if not info['hosted']:
        ui.write('(not running mozilla hooks on non-hosted repo)\n')
        return 0

    checks = get_checks(ui, repo, info, CHECKS)

    for check in checks:
        check.pre()

    for rev in repo.changelog.revs(repo[node].rev()):
        ctx = repo[rev]

        for check in checks:
            if not check.check(ctx):
                return 1

    for check in checks:
        if not check.post_check():
            return 1

    return 0


def reposetup(ui, repo):
    ui.setconfig('hooks', 'pretxnchangegroup.mozhooks', pretxnchangegroup)
