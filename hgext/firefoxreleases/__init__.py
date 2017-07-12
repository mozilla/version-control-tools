# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Expose Firefox release information."""

import collections
import os

from mercurial.i18n import _
from mercurial import (
    error,
    extensions,
    revset,
)
from mercurial.hgweb import (
    webcommands,
    webutil,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
execfile(os.path.join(OUR_DIR, '..', 'bootstrap.py'))

import mozautomation.releasedb as releasedb

from mozhg.util import (
    is_firefox_repo,
)

minimumhgversion = '4.1'
testedwith = '4.1 4.2 4.3'


def extsetup(ui):
    extensions.wrapfunction(webutil, 'changesetentry', changesetentry)

    setattr(webcommands, 'firefoxreleases', firefox_releases_web_command)
    webcommands.__all__.append('firefoxreleases')

    # TODO remove once we can use @revsetpredicate from extensions
    revset.symbols['firefoxrelease'] = revset_firefoxrelease
    revset.safesymbols.add('firefoxrelease')


def db_for_repo(repo):
    """Obtain a FirefoxReleaseDatabase for a repo or None."""
    if not repo.local():
        return None

    if not repo.ui.configbool('mozilla', 'enablefirefoxreleases', False):
        return None

    if not is_firefox_repo(repo):
        return None

    default = repo.vfs.join('firefoxreleases.db')
    path = repo.ui.config('mozilla', 'firefoxreleasesdb', default)

    if not os.path.exists(path):
        return None

    return releasedb.FirefoxReleaseDatabase(path)


def release_builds(db, repo, filter_unknown_revision=True):
    """Obtain Firefox release builds.

    By default, only builds associated with revisions in this repo are returned.
    """
    for build in db.builds():
        if filter_unknown_revision and build.revision not in repo:
            continue

        yield build


def release_builds_by_revision(db, repo):
    """Obtain builds indexed by integer revision."""
    by_rev = collections.defaultdict(list)

    for build in db.builds():
        try:
            ctx = repo[build.revision]
        except error.RepoLookupError:
            continue

        by_rev[ctx.rev()].append(build)

    return by_rev


def release_configurations(db, repo):
    """Obtain a set of release configurations seen in this repo.

    Essentially, finds the set of (channel, platform) tuples that are present
    in this repo.
    """
    return db.unique_release_configurations(
        fltr=lambda build: build.revision in repo)


def firefox_releases_web_command(web, req, tmpl):
    """Show information about Firefox releases."""
    repo = web.repo

    db = db_for_repo(repo)
    if not db:
        return tmpl('error', error='Firefox release info not available')

    platform = req.form['platform'][0] if 'platform' in req.form else None

    builds = []

    for build in release_builds(db, repo):
        if platform and build.platform != platform:
            continue

        builds.append(build)

    releases = []

    for i, build in enumerate(builds):
        entry = build._asdict()
        entry['parity'] = 'parity%d' % (i % 2)
        entry['anchor'] = build_anchor(build)
        releases.append(entry)

    return tmpl('firefoxreleases', releases=releases)


def release_config(build):
    return build.channel, build.platform


def build_anchor(build):
    return '%s%s%s%s' % (build.revision[0:12], build.channel, build.platform,
                         build.build_id)


def changesetentry(orig, web, req, tmpl, ctx):
    """Add metadata for an individual changeset in hgweb."""
    repo = web.repo

    d = orig(web, req, tmpl, ctx)

    db = db_for_repo(repo)
    if not db:
        return d

    releases = release_info_for_changeset(db, repo, ctx)

    if releases['this']:
        d['firefox_releases_here'] = []
        d['firefox_releases_first'] = []

        for config, build in sorted(releases['this'].items()):
            entry = build._asdict()

            entry['anchor'] = build_anchor(build)

            # Set links to previous and future releases.
            if config in releases['previous']:
                entry['previousnode'] = releases['previous'][config].revision

            d['firefox_releases_here'].append(entry)
            d['firefox_releases_first'].append(entry)

    if releases['future']:
        d.setdefault('firefox_releases_first', [])

        for config, build in sorted(releases['future'].items()):
            entry = build._asdict()

            entry['anchor'] = build_anchor(build)

            if entry not in d['firefox_releases_first']:
                d['firefox_releases_first'].append(entry)

    if releases['previous']:
        d['firefox_releases_last'] = []

        for config, build in sorted(releases['previous'].items()):
            entry = build._asdict()

            entry['anchor'] = build_anchor(build)

            d['firefox_releases_last'].append(entry)

    # Used so we don't display "first release with" and "last release without".
    # We omit displaying in this scenario because we're not confident in the
    # data and don't want to take chances with inaccurate data.
    if 'firefox_releases_first' in d and 'firefox_releases_last' in d:
        d['have_first_and_last_firefox_releases'] = True

    return d


def release_info_for_changeset(db, repo, ctx):
    """Given a changeset, obtain relevant release info."""
    # Find the previous release before this changeset. We walk ancestors
    # and store the first seen build entry for each release configuration.
    with db.cache_builds():
        revisions = release_builds_by_revision(db, repo)
        configs = release_configurations(db, repo)

    previous_releases = {}
    cl = repo.changelog

    for rev in cl.ancestors([ctx.rev()]):
        if rev not in revisions:
            continue

        for build in revisions[rev]:
            config = release_config(build)
            previous_releases.setdefault(config, build)

        # Found all release configurations. All previous releases identified.
        if len(configs) == len(previous_releases):
            break

    # Find releases on exactly this changeset.
    this_releases = {}

    for build in revisions.get(ctx.rev(), []):
        this_releases[release_config(build)] = build

    # Now find the first releases with this changeset. This is similar to above
    # except we "walk" descendants. Actual descendant walking can be slow
    # because data is indexed by ancestors. Since changelog data is ordered
    # and we have a mapping from revision to builds, we instead iterate over
    # future revisions. When we find a revision with builds, we verify the
    # start node is an ancestor otherwise we keep going.
    #
    # There is potential for this code to consume a lot of CPU. If the
    # start revision is early in the repo and we're searching for a config
    # that doesn't exist, we could perform many isancestor() checks as we
    # traverse to the end of the repo. This can be fixed by capping search
    # length. Another strategy would be conditionally checking isancestor()
    # if that revision has a config we're interested in. The latter is only
    # partial mitigation. But it might be good enough as a first step.
    # Of course, if the underlying data is append-only, then the mapping can
    # be cached.

    first_releases = dict(this_releases)

    for rev in cl.revs(ctx.rev()):
        if len(configs) == len(first_releases):
            break

        if rev not in revisions:
            continue

        # We're not walking descendants. Verify start rev actually is ancestor.
        if not cl.isancestor(ctx.node(), repo[rev].node()):
            continue

        for build in revisions[rev]:
            config = release_config(build)
            first_releases.setdefault(config, build)

    future_releases = {k: v for k, v in first_releases.items()
                       if k not in this_releases}

    return {
        'previous': previous_releases,
        'this': this_releases,
        'first': first_releases,
        'future': future_releases,
    }


def revset_firefoxrelease(repo, subset, x):
    """``firefoxrelease([channel=], [platform=])

    Changesets that have Firefox releases built from them.

    Accepts the following named arguments:

    channel
       Which release channel to look at. e.g. ``nightly``. Multiple channels
       can be delimited by spaces.
    platform
       Which platform to limit builds to. e.g. ``win32``. Multiple platforms
       can be delimited by spaces.

    If multiple filters are requested filters are combined using logical AND.

    If no filters are specified, all revisions having a Firefox release are
    matched.
    """
    args = revset.getargsdict(x, 'firefoxrelease', 'channel platform')

    channels = set()

    if 'channel' in args:
        channels = set(revset.getstring(args['channel'],
                                        _('channel requires a string')).split())

    platforms = set()

    if 'platform' in args:
        platforms = set(revset.getstring(args['platform'],
                                         _('platform requires a '
                                           'string')).split())

    db = db_for_repo(repo)
    if not db:
        repo.ui.warn(_('(warning: firefoxrelease() revset not available)\n'))
        return revset.baseset()

    def get_revs():
        for rev, builds in release_builds_by_revision(db, repo).iteritems():
            for build in builds:
                if channels and build.channel not in channels:
                    continue

                if platforms and build.platform not in platforms:
                    continue

                yield rev
                break

    return subset & revset.generatorset(get_revs())
