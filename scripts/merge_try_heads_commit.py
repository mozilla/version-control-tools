# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Create the dummy merge commits that collapse Try heads.

Each head named in the heads file is merged into a chain rooted at a base
revision, one merge commit per head. The commits are built in memory, so no
working directory is needed and the cost of a merge does not scale with the
number of files in the repository.

Every merge shares a single empty manifest. Returning an already-stored
manifest node from `manifestnode()` makes `commit._prepare_files()` take its
"reuse an existing manifest" fast path, so it never reads the manifests of
either parent and never calls `filectxfn`. That keeps each commit O(1)
instead of proportional to the size of the tree. This approach comes from
https://bugzilla.mozilla.org/show_bug.cgi?id=2043512.

This module lives apart from `merge_try_heads.py` so the driver can spawn it
as a subprocess, follow the merges it reports and stop it early. It imports
the stop handling from the driver rather than repeating it.

Each merge commit is reported on standard output as `<count> <node>` so the
caller can follow progress and learn the node to push. On `SIGINT` or
`SIGTERM` the run stops at the next commit boundary, keeping the merges made
so far. A second signal aborts at once, which rolls back the transaction in
flight but keeps the merges committed before it.
"""

import argparse
import binascii
import os
import sys
from typing import Any, List, Tuple

from mercurial import context, hg, localrepo, manifest, scmutil
from mercurial import ui as uimod
from merge_try_heads import StopRequest

COMMIT_MESSAGE = b"Merge try head"

# Number of merges committed per transaction. Batching keeps the transaction
# journal bounded without paying for a transaction on every commit.
BATCH_SIZE = 1000

stop_request = StopRequest()


class EmptyTreeMergeContext(context.memctx):
    """An in-memory merge commit whose tree is empty.

    Overriding `manifestnode()` to return a manifest that is already stored
    is what lets the commit skip reading its parents' manifests.
    """

    def __init__(
        self,
        repo: localrepo.localrepository,
        parents: Tuple[context.changectx, context.changectx],
        empty_manifest: bytes,
        username: bytes,
    ) -> None:
        super().__init__(
            repo,
            parents,
            COMMIT_MESSAGE,
            [],
            lambda *args: None,
            user=username,
        )
        self.empty_manifest = empty_manifest

    def manifestnode(self) -> bytes:
        return self.empty_manifest


def main() -> int:
    """Merge the heads listed in the heads file into the base revision."""
    arguments = parse_arguments()
    stop_request.install_handlers()

    repo = hg.repository(uimod.ui.load(), os.getcwdb())
    base = scmutil.revsingle(repo, arguments.base.encode("ascii"))
    heads = read_heads(arguments.heads_file)
    username = arguments.user.encode("utf-8") if arguments.user else repo.ui.username()

    merge_heads(repo, base, heads, username)

    return 0


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("base", help="Revision to merge the heads into.")
    parser.add_argument(
        "heads_file", help="File listing the head nodes to merge, one per line."
    )
    parser.add_argument(
        "--user",
        default=None,
        help="Author to record on the merge commits. Defaults to the Mercurial "
        "username, from `HGUSER`, `ui.username` or `EMAIL`.",
    )

    return parser.parse_args()


def read_heads(path: str) -> List[bytes]:
    """Return the head nodes listed in `path`, in the order given."""
    with open(path) as heads_file:
        return [
            binascii.unhexlify(line.strip().encode("ascii"))
            for line in heads_file
            if line.strip()
        ]


def merge_heads(
    repo: localrepo.localrepository,
    base: context.changectx,
    heads: List[bytes],
    username: bytes,
) -> context.changectx:
    """Commit one dummy merge per head, reporting each new commit."""
    parent = base
    empty_manifest = None
    merged = 0

    while merged < len(heads) and not stop_request.requested:
        batch_end = min(merged + BATCH_SIZE, len(heads))
        with repo.lock(), repo.transaction(b"merge-try-heads") as transaction:
            if empty_manifest is None:
                empty_manifest = write_empty_manifest(repo, transaction)

            for head in heads[merged:batch_end]:
                if stop_request.requested:
                    break

                parent = commit_merge(repo, parent, head, empty_manifest, username)
                merged += 1
                report(merged, parent)

    return parent


def write_empty_manifest(repo: localrepo.localrepository, transaction: Any) -> bytes:
    """Store the empty manifest that every merge commit points at."""
    return manifest.memmanifestctx(repo.manifestlog).write(
        transaction, len(repo), repo.nullid, repo.nullid, [], []
    )


def commit_merge(
    repo: localrepo.localrepository,
    parent: context.changectx,
    head: bytes,
    empty_manifest: bytes,
    username: bytes,
) -> context.changectx:
    """Create a single merge commit joining `parent` and `head`."""
    memctx = EmptyTreeMergeContext(repo, (parent, repo[head]), empty_manifest, username)

    return repo[memctx.commit()]


def report(count: int, parent: context.changectx) -> None:
    """Report a new merge commit so the caller can track progress and the tip."""
    node = binascii.hexlify(parent.node()).decode("ascii")
    print(f"{count} {node}", flush=True)


def run() -> int:
    """Run `main`, exiting quietly when a second signal aborts the run."""
    try:
        return main()
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(run())
