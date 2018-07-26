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
    error,
    hg,
    localrepo,
    repoview,
)

testedwith = '4.5 4.6'
minimumhgversion = '4.5'


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

    urepo = repo.unfiltered()
    cl = urepo.changelog
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
    # heads.
    #
    # In the common case, the set of replicated heads is the same as the
    # set of actual heads. Since this case is fast to check for, we do that
    # explicitly and short-circuit a DAG walk.
    #
    # If the set of heads are different, we use a revset to compute the
    # DAG difference between the 2 sets of heads and their ancestors.
    # Note that we cannot perform a simple DAG traversal while stopping
    # at replicated head revisions. The reason is that there is no guarantee
    # that the DAG ancestors occur in the replicated heads set. This can
    # occur when a new head is added to the repo, for example.

    cl_heads = cl.headrevs()

    if set(cl_heads) == replicated_head_revs:
        unreplicated_revs = set()

    else:
        unreplicated_revs = urepo.revs('::%ld - ::%ld', cl_heads,
                                       replicated_head_revs)

    return frozenset(unserved | set(unreplicated_revs))


def extsetup(ui):
    repoview.filtertable['replicatedserved'] = computeunreplicated

    # This tells the branchmap code that the branchmap cache for our custom
    # repoview is derived from the served repoview. It makes branchmap
    # cache generation a bit faster by allowing a partial calculation.
    # TODO this is buggy and causes exceptions. See
    # https://bugzilla.mozilla.org/show_bug.cgi?id=1470606#c35.
    #branchmap.subsettable['replicatedserved'] = 'served'

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
        @localrepo.repofilecache('replicated-data')
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
