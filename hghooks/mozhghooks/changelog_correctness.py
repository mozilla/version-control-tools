# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import textwrap
from cStringIO import StringIO
from mercurial.node import short

"""
Mercurial changeset objects store a list of changed paths. This allows
Mercurial to resolve which changesets changed which paths without having to
perform a secondary (and expensive) lookup by computing the delta between two
manifests. This is a really big deal for the Firefox repo because manifests are
large and accessing their data takes a long time in comparison to changeset
scanning.

The list of files in the changeset can be wrong due to a bug in mercurial
rebase.

We can't fix the issue in existing repos without changing SHA-1's. If we ever
rewrote history, we would want to fix this issue as part of the conversion.

But we can prevent more such broken changesets from entering history.
"""

def get_changed_files(repo, cs1, cs2):
    """
    Return the list of changed files between changeset cs1 and changeset
    cs2 (given as changectx) in the given repository.
    """
    # This is the simplest way to implement this with mercurial APIs,
    # but it's really too slow:
    #   modified, added, removed = repo.status(cs2.node(), cs1.node())[:3]
    #   changed_files = set(modified) | set(added) | set(removed)
    # Presumably, using repo.manifest.revdiff would be much faster, but
    # it raises exceptions when used on changesets part of the push.
    # So a manual diff of the manifests, as below, is faster.

    manifest1 = repo.manifest.revision(cs1.manifestnode())
    manifest2 = repo.manifest.revision(cs2.manifestnode())
    lines1 = iter(StringIO(manifest1))
    lines2 = iter(StringIO(manifest2))

    def get_next(lines):
        try:
            return lines.next()
        except StopIteration:
            return None

    changed_files = set()
    line1 = get_next(lines1)
    line2 = get_next(lines2)
    while True:
        if line1 == line2:
            if line2 is None:
                break
            line1 = get_next(lines1)
            line2 = get_next(lines2)
            continue
        if line1 is not None:
            f1, _ = line1.split('\0', 1)
        if line2 is not None:
            f2, _ = line2.split('\0', 1)

        if line1 is not None and line2 is not None and f1 == f2:
            changed_files.add(f2)
            line1 = get_next(lines1)
            line2 = get_next(lines2)
        elif line2 is None or line1 is not None and f1 < f2:
            changed_files.add(f1)
            line1 = get_next(lines1)
        else:
            changed_files.add(f2)
            line2 = get_next(lines2)

    return changed_files


def hook(ui, repo, node, source=None, **kwargs):
    if source in ('pull', 'strip'):
        return 0

    broken = []

    # All changesets from node to "tip" inclusive are part of this push.
    rev = repo.changectx(node).rev()
    tip = repo.changectx('tip').rev()
    for i in xrange(rev, tip + 1):
        ctx = repo.changectx(i)
        parents = ctx.parents()
        if len(parents) != 1:
            # Merge changesets don't store the same kind of file list.
            continue

        # Running this check thoroughly on all changesets reveals that all the
        # detected ones have a 'rebase_source' marker. As the test is rather
        # slow, skip changesets without such a marker.
        if 'rebase_source' not in ctx.extra():
            continue
        changed_files = get_changed_files(repo, parents[0], ctx)

        if changed_files != set(ctx.files()):
            broken.append(short(ctx.node()))

    if broken:
        ui.write(textwrap.dedent('''
            You apparently used `hg rebase` before pushing, and your mercurial
            version stores inconsistent metadata when doing so. Please upgrade
            mercurial or avoid `hg rebase`.
            Following is the list of changesets from your push with
            inconsistent metadata:
        '''))
        for c in broken:
            ui.write('   %s\n' % c)
        ui.write(textwrap.dedent('''
            See http://wiki.mozilla.org/Troubleshooting_Mercurial#Fix_rebase
            for possible instructions how to fix your push.
        '''))
        return 1

    return 0
