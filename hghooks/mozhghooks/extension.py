# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Mercurial extension to run hooks on repositories."""

from __future__ import absolute_import

from mercurial import (
    configitems,
    registrar,
)
from mozhg.util import (
    identify_repo,
    timers,
)

testedwith = b'4.8 4.9 5.0 5.1 5.2 5.3'
minimumhgversion = b'4.8'
buglink = b'https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org'

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'allowedroots', b'.*',
           generic=True)
configitem(b'mozilla', b'check.*',
           generic=True)
configitem(b'mozilla', b'repo_root',
           default=configitems.dynamicdefault)
configitem(b'mozilla', b'treeherder_repo',
           default=None)
configitem(b'mozilla', b'lando_required_repo_list',
           default=b'')
configitem(b'mozilla', b'direct_push_disabled_repo_list',
           default=b'')
configitem(b'mozilla', b'sentry_dsn',
           default=b"")
configitem(b'mozilla', b'check_bug_references_repos',
           default=None)
configitem(b'pushlog', b'autolanduser',
           default=b'bind-autoland@mozilla.com')
configitem(b'pushlog', b'landingworkeruser',
           default=b'lando_landing_worker@mozilla.com')


def get_check_classes(hook):
    # TODO come up with a mechanism for automatically discovering checks
    # so we don't have to enumerate them all.
    from mozhghooks.check import (
        advertise_upgrade,
        merge_day,
        prevent_cross_channel_messages,
        check_bug_references,
        prevent_subrepos,
        prevent_symlinks,
        prevent_sync_ipc_changes,
        prevent_webidl_changes,
        prevent_wptsync_changes,
        lando_required,
        single_root,
        try_task_config_file,
    )

    # TODO check to hook mapping should also be automatically discovered.
    if hook == b'pretxnchangegroup':
        return (
            merge_day.MergeDayCheck,
            prevent_cross_channel_messages.XChannelMessageCheck,
            prevent_subrepos.PreventSubReposCheck,
            prevent_symlinks.PreventSymlinksCheck,
            prevent_sync_ipc_changes.SyncIPCCheck,
            prevent_webidl_changes.WebIDLCheck,
            prevent_wptsync_changes.WPTSyncCheck,
            lando_required.LandoRequiredCheck,
            single_root.SingleRootCheck,
            try_task_config_file.TryConfigCheck,
        )

    elif hook == b'changegroup':
        return (
            advertise_upgrade.AdvertiseUpgradeCheck,
        )

    elif hook == b'pretxnclose':
        return (
            check_bug_references.CheckBugReferencesCheck,
        )


def get_checks(ui, repo, source, classes):
    """Loads checks from classes.

    Returns a list of check instances that are active for the given repo.
    """

    # Never apply hooks at pull time or when re-applying from strips.
    if source in (b'pull', b'strip'):
        return []

    info = identify_repo(repo)

    # Don't apply to non-hosted repos.
    if not info[b'hosted']:
        ui.write(b'(not running mozilla hooks on non-hosted repo)\n')
        return []

    checks = []

    for cls in classes:
        check = cls(ui, repo, info)
        name = check.name

        force_enable = False
        force_disable = False
        override = ui.config(b'mozilla', b'check.%s' % name)
        if override in (b'enable', b'true'):
            force_enable = True
        elif override in (b'disable', b'false'):
            force_disable = True

        enabled = check.relevant()
        if not isinstance(enabled, bool):
            raise Exception(b'relevant() must return a bool; got %s' % enabled)

        if enabled and force_disable:
            ui.warn(b'(%s check disabled per config override)\n' %
                    name)
            continue
        elif not enabled and force_enable:
            ui.warn(b'(%s check enabled per config override)\n' %
                    name)
            enabled = True

        if enabled:
            checks.append(check)

    return checks


def pretxnchangegroup(ui, repo, node, source=None, **kwargs):
    checks = get_checks(ui, repo, source,
                        get_check_classes(b'pretxnchangegroup'))

    with timers(ui, b'mozhooks', b'mozhooks.pretxnchangegroup.') as times:
        for check in checks:
            with times.timeit(check.name):
                check.pre(node)

        for rev in repo.changelog.revs(repo[node].rev()):
            ctx = repo[rev]

            for check in checks:
                with times.timeit(check.name):
                    if not check.check(ctx):
                        return 1

        for check in checks:
            with times.timeit(check.name):
                if not check.post_check():
                    return 1

        return 0


def pretxnclose(ui, repo, node=None, source=None, txnname=None, **kwargs):
    # Only run hooks on a `push` transaction. `commit`, etc are not relevant
    if txnname != b"push":
        return 0

    checks = get_checks(ui, repo, source,
                        get_check_classes(b'pretxnclose'))

    with timers(ui, b'mozhooks', b'mozhooks.pretxnclose.') as times:
        for check in checks:
            with times.timeit(check.name):
                check.pre(node)

        for rev in repo.changelog.revs(repo[node].rev()):
            ctx = repo[rev]

            for check in checks:
                with times.timeit(check.name):
                    if not check.check(ctx):
                        return 1

        for check in checks:
            with times.timeit(check.name):
                if not check.post_check():
                    return 1

        return 0


def changegroup(ui, repo, source=None, **kwargs):
    checks = get_checks(ui, repo, source, get_check_classes(b'changegroup'))

    with timers(ui, b'mozhooks', b'mozhooks.changegroup.') as times:
        for check in checks:
            with times.timeit(check.name):
                if not check.check(**kwargs):
                    return 1

        return 0


def reposetup(ui, repo):
    ui.setconfig(b'hooks', b'pretxnchangegroup.mozhooks', pretxnchangegroup)
    ui.setconfig(b'hooks', b'changegroup.mozhooks', changegroup)
    ui.setconfig(b'hooks', b'pretxnclose.mozhooks', pretxnclose)
