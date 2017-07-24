# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Sparse graphs for a revrange

When using graphmod directly to get the topology of a revrange,
it shows all connections in the underlying DAG, and not just
the topology inside the revrange. See the following example:

```
  $ hg log -G -r ::3 -T '{ rev }'
  o    3
  |\
  | o  2
  | |
  o |  1
  |/
  o  0
```

Now, if we only wanted 0, 1, and 3, graphmod gives

```
  $ hg log -G -r '::3 - 2' -T '{ rev }'
  o    3
  |\
  o :  1
  :/
  o  0
```

For the sparse graph, we want the minimal graph, i.e., we know that
we can get from 3 to 0 via 1. We're not interested that there's a
path in the underlying DAG that gets from 3 to 0 without going through
1.

"""

from collections import defaultdict
from mercurial import graphmod, scmutil, node


class SparseGraph(object):
    def __init__(self, source, src_revs):
        self.source = source
        self.src_revs = src_revs
        #: Mapping of revision ints to list of children
        self.children = defaultdict(list)
        #: Mapping of revision ints to list of parents
        self.parents = {}
        self.archived_parents = []
        #: list of merges, i.e. more than one parent
        self.merges = []
        #: list of forks, i.e. more than one child
        self.forks = []
        #: List of revisions with no parents in the sparse graph
        #: These do have parents in the original DAG
        self.roots = []
        #: Set of revisions with no children in the sparse graph
        #: These may have children in the orignal DAG
        self.heads = set()
        self.graph = None

    def createGraph(self, max_depth=1, optimize=True):
        """Create the sparse graph.

        max_depth: Direct grand-parent loops to detect and remove
        optimize: Find long-range loops and remove them from the
            graph. Requires at least max_depth of 1
        """
        self.parents.clear()
        self.heads.clear()
        del self.archived_parents[:]
        del self.merges[:]
        range = scmutil.revrange(self.source,  self.src_revs)
        self.graph = list(graphmod.dagwalker(self.source, range))
        gid2rev = dict(
            ((id, ctx.rev()) for id, C, ctx, parents in self.graph))
        # graphmod returns a graph of all possible connections through
        # the underlying original graph.
        # We want a minimal graph instead, that goes through our nodes if it
        # can.
        # get the full graph of all nodes first
        # we ignore missing parents, too, we collect those in self.roots
        for _id, C, src_ctx, parents in self.graph:
            local_parents = set((
                gid2rev.get(p[1]) for p in parents if p[0] != 'M'))
            self.parents[src_ctx.rev()] = local_parents

        # eliminate leap-frog loops where the grandchild is also a child
        # we do this for grandchildren, and deeper.
        # The depth is a bit of an optimization problem.

        def iterate_parents(parents, depth):
            # recursive parents helper
            if depth > 0:
                for p in parents:
                    for grandparents in \
                            iterate_parents(self.parents.get(p, []), depth-1):
                        yield grandparents
            else:
                yield parents

        for depth in xrange(1, max_depth + 1):
            self.archived_parents.append(self.parents)
            new_parents = {}
            for src_rev, local_parents in self.parents.items():
                minimal_parents = local_parents.copy()
                for parents in iterate_parents(local_parents, depth):
                    minimal_parents.difference_update(parents)
                new_parents[src_rev] = minimal_parents
            self.parents = new_parents

        # find heads, roots, merges, children and forks
        all_parents = set()
        for src_rev, local_parents in self.parents.items():
            if src_rev not in all_parents and src_rev is not node.nullrev:
                self.heads.add(src_rev)
            if not local_parents and src_rev is not node.nullrev:
                self.roots.append(src_rev)
            else:
                all_parents.update(local_parents)
                self.heads.difference_update(local_parents)
                if len(local_parents) > 1:
                    self.merges.append(src_rev)
            for c in local_parents:
                self.children[c].append(src_rev)
        self.forks = [rev for rev, children in self.children.items()
                      if len(children) > 1]
        if optimize:
            self.archived_parents.append(self.parents.copy())
            self.eliminateShortCuts()

    def eliminateShortCuts(self):
        '''Go through the graph and remove shortcut circles.
        '''
        major_childs = sorted(self.merges, key=lambda c: len(self.parents[c]))
        for child in major_childs:
            unhook = set()
            for parent in self.parents[child]:
                if self._eliminate(child, parent):
                    unhook.add(parent)
            if unhook:
                self.parents[child].difference_update(unhook)
                if len(self.parents[child]) == 1:
                    self.merges.remove(child)

    def _eliminate(self, child, parent):
        front = set(c for c in self.children[parent] if c < child)
        self.children[parent] = self.children[parent][:]
        while front:
            segs = [[c for c in self.children[p] if c <= child] for p in front]
            front = set(reduce(lambda a, b: a+b, segs, []))
            if child in front:
                self.children[parent].remove(child)
                if len(self.children[parent]) == 1:
                    self.forks.remove(parent)
                return True
        return False


class GraphWalker(object):
    '''Base class for iterating over SparseGraph objects.
    '''
    def __init__(self, graph):
        self.queue = None  # nodes to visit next
        self.visited = None  # nodes we've seen
        self.waiting = None  # these wait for some of their parents
        self.graph = graph

    def walkGraph(self):
        self.visited = {node.nullrev}
        self.waiting = set()
        self.queue = self.graph.roots[:]
        self.sortQueue()
        while self.queue:
            src_rev = self.queue.pop()
            if not self._shouldHandle(src_rev):
                continue
            self.visited.add(src_rev)
            self.waiting -= self.graph.parents[src_rev]
            self.handlerev(src_rev)
            children = self.graph.children[src_rev]
            for child in children:
                if self._shouldHandle(child):
                    self.queue.append(child)
                else:
                    self.waiting.add(src_rev)
            self.sortQueue()

    def _shouldHandle(self, src_rev):
        if src_rev in self.visited:
            return False
        for src_parent in self.graph.parents[src_rev]:
            if src_parent not in self.visited:
                # didn't process all parents yet, other roots should get here
                return False
        return True

    def sortQueue(self):
        self.queue.sort(reverse=True)

    def handlerev(self, src_rev):
        raise NotImplementedError
