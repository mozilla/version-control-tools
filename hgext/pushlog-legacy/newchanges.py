from mercurial import hg, cmdutil, util
from mercurial.node import hex, bin, nullid

def newchanges(ui, repo, oldrev, newrev='tip'):
    def isancestor(node, child):
        """Is the given node an ancestor of the child? returns True or False"""
        return repo.changelog.ancestor(child, node) == node

    oldrev = repo.lookup(oldrev)
    newrev = repo.lookup(newrev)

    displayer = cmdutil.show_changeset(ui, repo, {})

    reachable = {}

    def between(top, bottom):
        """repo.between doesn't seem to actually return *all* the changesets,
        just some of them. This returns all of them, dammit, including the
        top, but not the bottom."""
        while top != bottom:
            yield top;

            (p1, p2) = repo.changelog.parents(top)
            if p2 != nullid:
                raise hg.RepoError("between called on merge revision %s. p2: %s" % (hex(top), hex(p2)))

            top = p1

    def processtip(tip):
        (base, p1, p2) = repo.branches([tip])[0][1:]

        ancestor = repo.changelog.ancestor(base, oldrev)

        # Now compute a map of nodes that are ancestors of the oldrev, stopping
        # when we get back to the branch base

        reachable[ancestor] = 1
        reachable.update(repo.changelog.reachable(oldrev, ancestor))

        bt = between(tip, base)
        for c in bt:
            if c in reachable:
                break

            displayer.show(None, c)

        if not isancestor(base, oldrev):
            displayer.show(None, base)

        for c in (p1, p2):
            if not isancestor(c, oldrev):
                processtip(c)

    processtip(newrev)

cmdtable = {
    'newchanges': (newchanges, [], "hg newchanges oldrev [newrev]"),
}
