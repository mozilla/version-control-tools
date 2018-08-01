# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Extension for unifying the contents of related by separate repositories.

Using pushlog data, this extension can recreate a new repository that is
chronologically ordered by the push times from multiple source repositories.
In other words, it will recreate the repository as if it were a single
repository from the beginning.

The extension also has the ability to create bookmarks in the destination
repository.

This extension was created to unify the discrete Firefox repositories, which
are logically the same but existed as separate repositories for historical
reasons. For that reason, some config options and defaults may not be
appropriate for all repos.

Config Files
------------

Because the configuration for repository unification can be complicated,
a standalone config file is used to define the source repositories and
how they are integrated into the destination repository.

This config file uses the Mercurial config file parser (basically
an INI file). Sections in the config represent source repositories.
Each section can have the following entries:

path (required)
   The filesystem path of the repository.

   It must be a filesystem path.

pullrevs (optional)
   Revset defining which revisions to pull from this repo into the unified
   repo. By default, this is `0:tip`, which means to pull all revisions.

bookmark (optional)
   Name of bookmark to associate with the tip-most commit from this repo.

   If not defined, the section name will be used.

   By default, bookmarks will be created.

nobookmark (optional)
   If defined, no bookmark will be defined for revisions coming from this
   repo.

The [GLOBAL] section defines special global settings. The following settings
can be defined:

stagepath (required)
   Local filesystem path to the repository that will hold contents of all
   source repositories.

   Every changeset from every source repository will be pulled into this repo.
   This provides a common source for adding changesets to the destination repo.

destpath (required)
   Local filesystem path to the final, destination repository.
"""

from __future__ import absolute_import

import collections
import gc
import os

from mercurial.node import (
    bin,
)
from mercurial import (
    bookmarks,
    config,
    cmdutil,
    error,
    exchange,
    extensions,
    hg,
    registrar,
    util,
)


cmdtable = {}

# Mercurial 4.3 introduced registrar.command as a replacement for
# cmdutil.command.
if util.safehasattr(registrar, 'command'):
    command = registrar.command(cmdtable)
else:
    command = cmdutil.command(cmdtable)


class unifyconfig(object):
    def __init__(self, path):
        self._c = config.config()
        with open(path, 'rb') as fh:
            self._c.read(path, fh)

        if 'GLOBAL' not in self._c:
            raise error.Abort('config file missing GLOBAL section')

        self.stagepath = self._c.get('GLOBAL', 'stagepath')
        if not self.stagepath:
            raise error.Abort('GLOBAL.stagepath not defined in config')

        self.destpath = self._c.get('GLOBAL', 'destpath')
        if not self.destpath:
            raise error.Abort('GLOBAL.destpath not defined in config')

    @property
    def sources(self):
        for name in sorted(self._c):
            # uppercase names are reserved for special sections.
            if name.upper() == name:
                continue

            bookmark = self._c.get(name, 'bookmark', name)
            if self._c.hasitem(name, 'nobookmark'):
                bookmark = None

            path = self._c.get(name, 'path')
            if not path:
                raise error.Abort('section %s missing "path"' % name)

            yield {
                'name': name,
                'path': path,
                'pullrevs': self._c.get(name, 'pullrevs', '0:tip'),
                'bookmark': bookmark,
            }


def emitfastforwardnodes(repo, pushtonode):
    """Given info about the pushes for every node, emit tip-most fast forward nodes.

    Basically, emit a node if its DAG branch is different from the DAG branch of
    the previous node. We can pull the emitted node to recreate a repository in
    push order as if all pushes went to the same repo using the minimum number
    of pull operations.
    """
    cl = repo.changelog
    relevantnodes = set(pushtonode.values())

    # We pre-populate the mapping of node to children by iterating the repo
    # and looking at parents because this lookup is indexed and much faster.
    # node -> set<node>
    clchildren = collections.defaultdict(set)
    for rev in repo:
        node = cl.node(rev)
        if node not in relevantnodes:
            continue

        for p in cl.parents(node):
            clchildren[p].add(node)

    wantedchildren = set()
    lastnode = None

    for key, node in sorted(pushtonode.items()):
        children = clchildren[node]

        # We're a DAG head. Always emit.
        if not children:
            yield node
            wantedchildren = set()
            lastnode = None
            continue

        # If this node is a child of the last node, keep going.
        if node in wantedchildren:
            lastnode = node
            wantedchildren = children
            continue

        # We aren't a child of the last node. That means we changed DAG
        # branches. So emit.
        if lastnode:
            yield lastnode

        lastnode = node
        wantedchildren = children

    # The loop should emit if there is a DAG head. And the last node should
    # always be a DAG head.
    assert lastnode is None


def unifypushes(pushtonode):
    """Given a mapping of original push info to node, create a new pushlog.

    This emits tuples of (source, pushid, who, when, [nodes]).
    """
    lastsource = None
    lastid = None
    lastwhen = None
    lastwho = None
    nodes = []

    for (when, source, rev, who, pushid), node in sorted(pushtonode.items()):
        # First time through.
        if lastsource is None:
            lastsource = source
            lastid = pushid
            lastwhen = when
            lastwho = who
            nodes.append(node)
            continue

        # Pushlog entries are unique by source repo and push id. Do not compare
        # time here because it is possible for different pushes to have the same
        # time (in theory) and we want to preserve these as separate events.
        if lastsource == source and lastid == pushid:
            nodes.append(node)
            continue

        yield lastsource, lastid, lastwho, lastwhen, nodes

        lastsource = source
        lastid = pushid
        lastwhen = when
        lastwho = who
        nodes = [node]

    if lastsource:
        yield lastsource, lastid, lastwho, lastwhen, nodes

def newpushes(repo, unifiedpushes):
    """Obtain push records for the unified destination repo.

    The output of this function should be fed into pushlog.recordpushes()
    to insert the new push records.
    """
    pushlog = repo.pushlog
    lastpushid = pushlog.lastpushid()

    destpushes = list(pushlog.pushes())
    destpushnodes = set()
    for push in destpushes:
        destpushnodes |= set(bin(n) for n in push.nodes)

    for source, pushid, who, when, nodes in unifiedpushes:
        missing = [n for n in nodes if n not in destpushnodes]
        if not missing:
            continue

        lastpushid += 1
        yield lastpushid, who, when, missing


@command('unifyrepo', [
    ], 'unifyrepo settings',
    norepo=True)
def unifyrepo(ui, settings):
    """Unify the contents of multiple source repositories using settings.

    The settings file is a Mercurial config file (basically an INI file).
    """
    conf = unifyconfig(settings)

    # Ensure destrepo is created with generaldelta enabled.
    ui.setconfig('format', 'usegeneraldelta', True)
    ui.setconfig('format', 'generaldelta', True)

    # Verify all source repos have the same revision 0
    rev0s = set()
    for source in conf.sources:
        repo = hg.repository(ui, path=source['path'])

        # Verify
        node = repo[0].node()
        if rev0s and node not in rev0s:
            ui.warn('repository has different rev 0: %s\n' % source['name'])

        rev0s.add(node)

    # Ensure the staging repo has all changesets from the source repos.

    stageui = ui.copy()

    # Enable aggressive merge deltas on the stage repo to minimize manifest delta
    # size. This could make delta chains very long. So we may want to institute a
    # delta chain cap on the destination repo. But this will ensure the stage repo
    # has the most efficient/compact representation of deltas. Pulling from this
    # repo will also inherit the optimal delta, so we don't need to enable
    # aggressivemergedeltas on the destination repo.
    stageui.setconfig('format', 'aggressivemergedeltas', True)

    stagerepo = hg.repository(stageui, path=conf.stagepath,
                              create=not os.path.exists(conf.stagepath))

    for source in conf.sources:
        path = source['path']
        sourcepeer = hg.peer(ui, {}, path)
        ui.write('pulling %s into %s\n' % (path, conf.stagepath))
        exchange.pull(stagerepo, sourcepeer)

    # Now collect all the changeset data with pushlog info.
    # node -> (when, source, rev, who, pushid)
    nodepushinfo = {}
    pushcount = 0
    allnodes = set()

    # Obtain pushlog data from each source repo. We obtain data for every node
    # and filter later because we want to be sure we have the earliest known
    # push data for a given node.
    for source in conf.sources:
        sourcerepo = hg.repository(ui, path=source['path'])
        pushlog = getattr(sourcerepo, 'pushlog', None)
        if not pushlog:
            raise error.Abort('pushlog API not available',
                              hint='is the pushlog extension loaded?')

        index = sourcerepo.changelog.index
        revnode = {}
        for rev in sourcerepo:
            # revlog.node() is too slow. Use the index directly.
            node = index[rev][7]
            revnode[rev] = node
            allnodes.add(node)

        noderev = {v: k for k, v in revnode.iteritems()}

        localpushcount = 0
        pushnodecount = 0
        for pushid, who, when, nodes in pushlog.pushes():
            pushcount += 1
            localpushcount += 1
            for node in nodes:
                pushnodecount += 1
                bnode = bin(node)

                # There is a race between us iterating the repo and querying the
                # pushlog. A new changeset could be written between when we
                # obtain nodes and encounter the pushlog. So ignore pushlog
                # for nodes we don't know about.
                if bnode not in noderev:
                    ui.warn('pushlog entry for unknown node: %s; '
                            'possible race condition?\n' % node)
                    continue

                rev = noderev[bnode]

                if bnode not in nodepushinfo:
                    nodepushinfo[bnode] = (when, path, rev, who, pushid)
                else:
                    currentwhen = nodepushinfo[bnode][0]
                    if when < currentwhen:
                        nodepushinfo[bnode] = (when, path, rev, who, pushid)

        ui.write('obtained pushlog info for %d/%d revisions from %d pushes from %s\n' % (
                 pushnodecount, len(revnode), localpushcount, source['name']))

    # Now verify that every node in the source repos has pushlog data.
    missingpl = allnodes - set(nodepushinfo.keys())
    if missingpl:
        raise error.Abort('missing pushlog info for %d nodes\n' % len(missingpl))

    # Filter out changesets we aren't aggregating.
    # We also use this pass to identify which nodes to bookmark.
    books = {}
    sourcenodes = set()
    for source in conf.sources:
        sourcerepo = hg.repository(ui, path=source['path'])
        cl = sourcerepo.changelog
        index = cl.index

        sourcerevs = sourcerepo.revs(source['pullrevs'])
        sourcerevs.sort()
        headrevs = set(cl.headrevs())
        sourceheadrevs = headrevs & set(sourcerevs)

        # We /could/ allow multiple heads from each source repo. But for now
        # it is easier to limit to 1 head per source.
        if len(sourceheadrevs) > 1:
            raise error.Abort('%s has %d heads' % (source['name'], len(sourceheadrevs)),
                              hint='define pullrevs to limit what is aggregated')

        for rev in cl:
            if rev not in sourcerevs:
                continue

            node = index[rev][7]
            sourcenodes.add(node)
            if source['bookmark']:
                books[source['bookmark']] = node

        ui.write('aggregating %d/%d revisions for %d heads from %s\n' % (
                 len(sourcerevs), len(cl), len(sourceheadrevs), source['name']))

    nodepushinfo = {k: v for k, v in nodepushinfo.iteritems() if k in sourcenodes}

    ui.write('aggregating %d/%d nodes from %d original pushes\n' % (
             len(nodepushinfo), len(allnodes), pushcount))

    # We now have accounting for every changeset. Because pulling changesets
    # is a bit time consuming, it is worthwhile to minimize the number of pull
    # operations. We do this by ordering all changesets by original push time
    # then emitting the minimum number of "fast forward" nodes from the tip
    # of each linear range inside that list.

    # (time, source, rev, user, pushid) -> node
    inversenodeinfo = {v: k for k, v in nodepushinfo.iteritems()}

    destui = ui.copy()
    destui.setconfig('format', 'aggressivemergedeltas', True)
    destui.setconfig('format', 'maxchainlen', 10000)

    destrepo = hg.repository(destui, path=conf.destpath,
                             create=not os.path.exists(conf.destpath))
    destcl = destrepo.changelog
    pullpushinfo = {k: v for k, v in inversenodeinfo.iteritems() if not destcl.hasnode(v)}

    ui.write('%d/%d nodes will be pulled\n' % (len(pullpushinfo), len(inversenodeinfo)))

    pullnodes = list(emitfastforwardnodes(stagerepo, pullpushinfo))
    unifiedpushes = list(unifypushes(inversenodeinfo))

    ui.write('consolidated into %d pulls from %d unique pushes\n' % (
             len(pullnodes), len(unifiedpushes)))

    if not pullnodes:
        ui.write('nothing to do; exiting\n')
        return

    stagepeer = hg.peer(ui, {}, conf.stagepath)

    for node in pullnodes:
        # TODO Bug 1265002 - we should update bookmarks when we pull.
        # Otherwise the changesets will get replicated without a bookmark
        # and any poor soul who pulls will see a nameless head.
        exchange.pull(destrepo, stagepeer, heads=[node])
        # For some reason there is a massive memory leak (10+ MB per
        # iteration on Firefox repos) if we don't gc here.
        gc.collect()

    # Now that we've aggregated all the changesets in the destination repo,
    # define the pushlog entries.
    pushlog = getattr(destrepo, 'pushlog', None)
    if not pushlog:
        raise error.Abort('pushlog API not available',
                          hint='is the pushlog extension loaded?')

    with destrepo.lock():
        with destrepo.transaction('pushlog') as tr:
            insertpushes = list(newpushes(destrepo, unifiedpushes))
            ui.write('inserting %d pushlog entries\n' % len(insertpushes))
            pushlog.recordpushes(insertpushes, tr=tr)

    # Verify that pushlog time in revision order is always increasing.
    destnodepushtime = {}
    for push in destrepo.pushlog.pushes():
        for node in push.nodes:
            destnodepushtime[bin(node)] = push.when

    destcl = destrepo.changelog
    lastpushtime = 0
    for rev in destrepo:
        node = destcl.node(rev)
        pushtime = destnodepushtime[node]

        if pushtime < lastpushtime:
            ui.warn('push time for %d is older than %d\n' % (rev, rev - 1))

        lastpushtime = pushtime

    # Write bookmarks.
    ui.write('writing %d bookmarks\n' % len(books))

    with destrepo.lock():
        with destrepo.transaction('bookmarks') as tr:
            bm = bookmarks.bmstore(destrepo)
            # Mass replacing may not be the proper strategy. But it works for
            # our current use case.
            bm.clear()
            bm.applychanges(destrepo, tr, books.items())

    # This is a bit hacky. Pushlog and bookmarks aren't currently replicated
    # via the normal hooks mechanism because we use the low-level APIs to
    # write them. So, we send a replication message to sync the entire repo.
    try:
        vcsr = extensions.find('vcsreplicator')
    except KeyError:
        raise error.Abort('vcsreplicator extension not installed; '
                          'pushlog and bookmarks may not be replicated properly')

    vcsr.replicatecommand(destrepo.ui, destrepo)
