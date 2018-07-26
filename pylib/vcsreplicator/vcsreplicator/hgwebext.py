# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""hgweb extension for vcsreplicator"""

from __future__ import absolute_import

import errno

# TRACKING hg46 use module bundles with Mercurial.
import cbor2

from mercurial.i18n import _
from mercurial.node import (
    hex,
)
from mercurial import (
    branchmap,
    dagutil,
    error,
    hg,
    localrepo,
    repoview,
)

testedwith = '4.5 4.6'
minimumhgversion = '4.5'


def log(repo, *args):
    if 'try' not in repo.root:
        return

    repo.ui.log('vcsreplicator', '%r: %s' % (repo.filtername, args[0]),
                *args[1:])


def computeunreplicated(repo, visibilityexceptions=None):
    """Compute the set of filtered revisions for exclusion from hgweb.

    This is the union of unserved revisions (from the "served" view) and the
    set of revisions that are children of heads listed in the
    ``replicated-heads`` file.
    """

    # We first filter out secret and hidden changesets, which is the default
    # behavior of hgweb.
    unserved = repoview.computeunserved(
        repo, visibilityexceptions=visibilityexceptions)

    data = repo.replicated_data

    # The file doesn't exist or is empty. This can happen if e.g. the heads
    # message has never been written out because a push hasn't occurred. Since
    # the replicated data feature is to reduce the inconsistency window
    # after pushes, if there has been no push, then there's no
    # inconsistency window. Just return the unserved set.
    if data is None:
        return unserved

    cl = repo.unfiltered().changelog
    clrev = cl.rev
    replicated_head_revs = set()

    for node in data[b'heads']:
        try:
            replicated_head_revs.add(clrev(node))

        # Having a node referenced in the file that doesn't exist in the
        # unfiltered repo is really weird. But it could conceivably happen
        # in weird conditions. Let's log it and treat it as non-fatal.
        except error.LookupError:
            repo.ui.log('vcsreplicator',
                        _('node in replicated data file does not exist: %s\n') %
                        hex(node))

    # Find the set of revisions between the changelog's heads and the replicated
    # heads, also excluding already filtered revisions. We use
    # ``revlogdag.ancestorset`` for this. This function essentially iterates
    # over starting revisions and walks ancestors until we find a revision in
    # a stop set or encounter an already seen revision. Parent revisions are
    # indexed, so ancestry walking is fast (as opposed to child walking,
    # which isn't indexed and is slow).
    #
    # In the common case, a push has not recently occurred: all DAG heads will
    # already be present in the stop set and this will simply do a set lookup
    # for each DAG head. That should be fast.
    #
    # In the uncommon case, we perform a DAG walk for each unreplicated head.
    # This will take time in proportion to the unreplicated DAG size, which
    # is often small.
    dag = dagutil.revlogdag(cl)
    unreplicated_revs = dag.ancestorset(cl.headrevs(),
                                        stops=replicated_head_revs | unserved)

    return frozenset(unserved | unreplicated_revs)


# This is a copy of branchmap.updatecache from Mercurial 4.5.3. This is
# here so we can debug exceptions.
def updatecache(repo):
    log(repo, 'updating branch cache\n')

    cl = repo.changelog
    filtername = repo.filtername
    partial = repo._branchcaches.get(filtername)

    if partial is None:
        log(repo, 'no partial cache\n')
    elif not partial.validfor(repo):
        log(repo, 'partial cache not valid\n')

    revs = []
    if partial is None or not partial.validfor(repo):
        partial = branchmap.read(repo)
        if partial is None:
            log(repo, 'no existing branchmap\n')
        else:
            log(repo, 'have partial branchmap\n')

        if partial is None:
            subsetname = branchmap.subsettable.get(filtername)
            if subsetname is None:
                partial = branchmap.branchcache()
            else:
                subset = repo.filtered(subsetname)
                partial = subset.branchmap().copy()
                extrarevs = subset.changelog.filteredrevs - cl.filteredrevs
                revs.extend(r for  r in extrarevs if r <= partial.tiprev)

    log(repo, 'extending revs from %d\n', partial.tiprev + 1)

    revs.extend(cl.revs(start=partial.tiprev + 1))

    log(repo, 'updating cache for %d revs: %d to %d\n', len(revs),
        revs[0] if revs else -1, revs[-1] if revs else -1)

    if revs:
        partial.update(repo, revs)
        partial.write(repo)

    assert partial.validfor(repo), filtername
    repo._branchcaches[repo.filtername] = partial


def extsetup(ui):
    repoview.filtertable['replicatedserved'] = computeunreplicated

    # This tells the branchmap code that the branchmap cache for our custom
    # repoview is derived from the served repoview. It makes branchmap
    # cache generation a bit faster by allowing a partial calculation.
    # TODO this is buggy and causes exceptions. See
    # https://bugzilla.mozilla.org/show_bug.cgi?id=1470606#c35.
    #branchmap.subsettable['replicatedserved'] = 'served'

    # Replace branchmap.updatecache with our version.
    branchmap.updatecache = updatecache

    # hgweb caches repository instances. And it determines whether instances
    # need to be reconstructed by stat()ing files listed in ``hg.foi`` at
    # request time. We add ``.hg/replicated-data`` to this list to ensure
    # that changes to the file are reflected on the next request and that
    # old cached state of this file/attribute aren't used.
    REFRESH_ENTRY = ('path', 'replicated-data')

    if REFRESH_ENTRY not in hg.foi:
        hg.foi.append(REFRESH_ENTRY)


def reposetup(ui, repo):
    if not repo.local():
        return

    class replicatedrepo(repo.__class__):
        # The property value will be cached until the repo's file caches are
        # invalidated. (The file is *not* stat()ed on every attribute access.)
        # This typically only occurs if the repository mutates itself. If
        # another process mutates the file, it will not be reflected on this
        # repository instance.
        #@localrepo.repofilecache('replicated-data')

        # Testing with a regular @property to isolate intermittent failures
        # in CI.
        @property
        def replicated_data(self):
            """Obtain the data structure holding fully replicated data.

            Returns None if the file does not exist or is empty.
            """
            try:
                raw_data = self.vfs.read(b'replicated-data')
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise

                return None

            # If empty, treat as missing.
            if not raw_data:
                return None

            try:
                data = cbor2.loads(raw_data)
            except cbor2.CBORDecodeError as e:
                raise error.Abort('malformed CBOR data: %s' % e)

            return data

    repo.__class__ = replicatedrepo
