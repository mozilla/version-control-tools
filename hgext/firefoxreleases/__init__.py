# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Expose Firefox release information."""

import collections
import os

from mercurial.i18n import _
from mercurial import (
    configitems,
    error,
    extensions,
    pycompat,
    registrar,
    revset,
    templateutil,
)
from mercurial.hgweb import (
    webcommands,
    webutil,
)

OUR_DIR = os.path.normpath(os.path.dirname(__file__))
with open(os.path.join(OUR_DIR, "..", "bootstrap.py")) as f:
    exec(f.read())

import mozautomation.releasedb as releasedb

from mozhg.util import (
    is_firefox_repo,
)


minimumhgversion = b"4.8"
testedwith = b"4.8 4.9 5.0 5.1 5.2 5.3 5.4 5.5 5.9"

configtable = {}
configitem = registrar.configitem(configtable)

configitem(
    b"mozilla",
    b"enablefirefoxreleases",  # deprecated, use firefox_releasing
    default=configitems.dynamicdefault,
)
configitem(b"mozilla", b"firefox_releasing", default=configitems.dynamicdefault)
configitem(b"mozilla", b"firefoxreleasesdb", default=configitems.dynamicdefault)

revsetpredicate = registrar.revsetpredicate()


def extsetup(ui):
    extensions.wrapfunction(webutil, "changesetentry", changesetentry)

    webcommands.firefoxreleases = webcommands.webcommand(b"firefoxreleases")(
        firefox_releases_web_command
    )


def db_for_repo(repo):
    """Obtain a FirefoxReleaseDatabase for a repo or None."""
    if not repo.local():
        return None

    if not repo.ui.configbool(
        b"mozilla", b"enablefirefoxreleases", False
    ) and not repo.ui.configbool(  # deprecated
        b"mozilla", b"firefox_releasing", False
    ):
        return None

    if not is_firefox_repo(repo):
        return None

    default = repo.vfs.join(b"firefoxreleases.db")
    path = repo.ui.config(b"mozilla", b"firefoxreleasesdb", default)

    if not os.path.exists(path):
        return None

    return releasedb.FirefoxReleaseDatabase(
        pycompat.sysstr(path), bytestype=pycompat.bytestr
    )


def release_builds(db, repo, filter_unknown_revision=True):
    """Obtain Firefox release builds.

    By default, only builds associated with revisions in this repo are returned.
    """
    for build in db.builds():
        if filter_unknown_revision and build[b"revision"] not in repo:
            continue

        yield build


def release_builds_by_revision(db, repo):
    """Obtain builds indexed by integer revision."""
    by_rev = collections.defaultdict(list)

    for build in db.builds():
        try:
            ctx = repo[build[b"revision"]]
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
        fltr=lambda build: build[b"revision"] in repo
    )


def _releases_mapped_generator(context, builds):
    """Generates build object mappings for use in the template layer"""
    for i, build in enumerate(builds):
        build[b"parity"] = pycompat.bytestr(i % 2)
        build[b"anchor"] = releasedb.build_anchor(build)
        yield build


def firefox_releases_web_command(web):
    """Show information about Firefox releases."""

    req = web.req

    repo = web.repo

    db = db_for_repo(repo)
    if not db:
        error_message = b"Firefox release info not available"
        return web.sendtemplate(b"error", error=error_message)

    platform = req.qsparams[b"platform"] if b"platform" in req.qsparams else None
    builds = []

    for build in release_builds(db, repo):
        if platform and build[b"platform"] != platform:
            continue

        builds.append(build)

    releases_mapping_generator = templateutil.mappinggenerator(
        _releases_mapped_generator, args=(builds,)
    )

    return web.sendtemplate(b"firefoxreleases", releases=releases_mapping_generator)


def release_config(build):
    return build[b"channel"], build[b"platform"]


def changesetentry(orig, web, ctx):
    """Add metadata for an individual changeset in hgweb."""
    d = orig(web, ctx)

    d = pycompat.byteskwargs(d)

    repo = web.repo

    db = db_for_repo(repo)
    if not db:
        return pycompat.strkwargs(d)

    releases = release_info_for_changeset(db, repo, ctx)

    if releases[b"this"]:
        d[b"firefox_releases_here"] = []
        d[b"firefox_releases_first"] = []

        for config, build in sorted(releases[b"this"].items()):
            build[b"anchor"] = releasedb.build_anchor(build)

            # Set links to previous and future releases.
            if config in releases[b"previous"]:
                build[b"previousnode"] = releases[b"previous"][config][b"revision"]

            d[b"firefox_releases_here"].append(build)
            d[b"firefox_releases_first"].append(build)

    if releases[b"future"]:
        d.setdefault(b"firefox_releases_first", [])

        for config, build in sorted(releases[b"future"].items()):
            build[b"anchor"] = releasedb.build_anchor(build)

            if build not in d[b"firefox_releases_first"]:
                d[b"firefox_releases_first"].append(build)

    if releases[b"previous"]:
        d[b"firefox_releases_last"] = []

        for config, build in sorted(releases[b"previous"].items()):
            build[b"anchor"] = releasedb.build_anchor(build)

            d[b"firefox_releases_last"].append(build)

    # Used so we don't display "first release with" and "last release without".
    # We omit displaying in this scenario because we're not confident in the
    # data and don't want to take chances with inaccurate data.
    if b"firefox_releases_first" in d and b"firefox_releases_last" in d:
        d[b"have_first_and_last_firefox_releases"] = True

    # Do some template fixes
    # TODO build via a generator
    if b"firefox_releases_first" in d:
        d[b"firefox_releases_first"] = templateutil.mappinglist(
            d[b"firefox_releases_first"]
        )

    if b"firefox_releases_last" in d:
        d[b"firefox_releases_last"] = templateutil.mappinglist(
            d[b"firefox_releases_last"]
        )

    if b"firefox_releases_here" in d:
        d[b"firefox_releases_here"] = templateutil.mappinglist(
            d[b"firefox_releases_here"]
        )

    return pycompat.strkwargs(d)


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

    future_releases = {
        k: v for k, v in first_releases.items() if k not in this_releases
    }

    return {
        b"previous": previous_releases,
        b"this": this_releases,
        b"first": first_releases,
        b"future": future_releases,
    }


@revsetpredicate(b"firefoxrelease")
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
    args = revset.getargsdict(x, b"firefoxrelease", b"channel platform")

    channels = set()

    if b"channel" in args:
        channels = set(
            revset.getstring(args[b"channel"], _(b"channel requires a string")).split()
        )

    platforms = set()

    if b"platform" in args:
        platforms = set(
            revset.getstring(
                args[b"platform"], _(b"platform requires a string")
            ).split()
        )

    db = db_for_repo(repo)
    if not db:
        repo.ui.warn(_(b"(warning: firefoxrelease() revset not available)\n"))
        return revset.baseset()

    def get_revs():
        for rev, builds in release_builds_by_revision(db, repo).items():
            for build in builds:
                if channels and build[b"channel"] not in channels:
                    continue

                if platforms and build[b"platform"] not in platforms:
                    continue

                yield rev
                break

    return subset & revset.generatorset(get_revs())
