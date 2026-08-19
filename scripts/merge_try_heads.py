#!/usr/bin/env -S uv run --script
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

# Mercurial is declared here because `merge_try_heads_commit.py` imports it and
# is spawned with this script's interpreter. The pin tracks the one in the
# repository's `pyproject.toml`.
# /// script
# requires-python = ">=3.9"
# dependencies = ["mercurial==7.2.2"]
# ///

"""Collapse the heads of the Try repository via dummy merges.

Try grows a new head with every push and several Mercurial operations get
slower as heads accumulate, so old heads are periodically merged away. See
`docs/hgmo/ops.rst`.

`mozilla-unified` is cloned as a seed, Try's heads are read from its
`json-log` endpoint, and those heads are pulled in small batches.
`merge_try_heads_commit.py` then merges them, building commits in
memory so no working directory is needed.
"""

import argparse
import json
import logging
import os
import pathlib
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from types import FrameType
from typing import Any, Callable, Iterator, List, Optional, Set, Tuple

logger = logging.getLogger("merge-try-heads")

MERGE_HELPER = pathlib.Path(__file__).resolve().parent / "merge_try_heads_commit.py"

HELP_EPILOG = """
Nothing is ever pushed; the push command is printed instead.

  # Pull Try's heads, then merge them.
  uv run --script scripts/merge_try_heads.py ~/try-merge

  # Merge the heads already in the clone, fetching nothing.
  uv run --script scripts/merge_try_heads.py ~/try-merge --no-pull

mozilla-unified is cloned as the seed and Try's heads are merged into its
`central` bookmark. WORKDIR is created if missing and reused if present, so a
run resumes rather than starting over.

WORKDIR.hgrc is generated alongside it holding only your ui.username, and hg
reads that instead of your own configuration. Extensions a Mozilla developer
normally enables get in the way: firefoxtree rewrites bookmarks on every
pull, mozext walks every changeset a pull adds, and pushlog aborts pulls.

Batch size is the setting that matters. Large responses from Try are
truncated by the CDN, so a batch carrying too much fails however often it is
retried. Batches that keep failing are deferred to
WORKDIR/.hg/merge-try-heads/deferred-heads and retried by the next run, which
regroups them with different neighbours. A
batch of 25 gets roughly 90% of batches through where 200 gets 40%.
"""

# Try is read and pulled over HTTPS because the head list comes from an HTTP
# endpoint, and pushed over SSH.
CLONE_URL = "https://hg.mozilla.org/mozilla-unified"
TRY_URL = "https://hg.mozilla.org/try"
TRY_PUSH_URL = "ssh://hg.mozilla.org/try"

DEFAULT_BATCH_SIZE = 25

# Identity recorded on the merge commits when the operator has none of their
# own configured, so an unattended run still has an author to commit as.
DEFAULT_USERNAME = "Try head merge <hgmo-service-discuss@mozilla.com>"

# The heads to collapse, and the revision they are merged into. The seed
# repository publishes a `central` bookmark at the `mozilla-central` tip.
HEADS_REVSET = "head() and branch(default) and not public()"
BASE_REVSET = "central"

# `json-log` returns 20 entries unless `revcount` asks for more, and Try has
# tens of thousands of heads.
JSON_LOG_REVCOUNT = 1000000
JSON_LOG_TIMEOUT = 600

CLONE_ATTEMPTS = 10
PULL_ATTEMPTS = 3
BASE_DELAY = 15.0
MAX_DELAY = 600.0

PROGRESS_INTERVAL = 100

# The all-zeroes node, reported as the tip of a repository with no changesets.
NULL_NODE = "0" * 40

# State this script keeps between runs. It is written inside the clone's `.hg`
# directory so the files never turn up as untracked files in the repository.
STATE_DIRNAME = "merge-try-heads"
HEADS_FILENAME = "heads"
MERGE_TIP_FILENAME = "merge-tip"
DEFERRED_FILENAME = "deferred-heads"


class StopRequest:
    """Tracks a request to stop merging at the next commit boundary."""

    def __init__(self) -> None:
        self.requested = False

    def install_handlers(self) -> None:
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum: int, frame: Optional[FrameType]) -> None:
        """Record the request, or abort outright if one is already pending."""
        if self.requested:
            raise KeyboardInterrupt

        self.requested = True
        logger.warning(
            "Stop requested. Finishing the merge in flight, then stopping. "
            "Signal again to abort immediately."
        )


stop_request = StopRequest()


def main() -> int:
    arguments = parse_arguments()
    configure_logging(arguments.verbose)
    stop_request.install_handlers()

    clone_path = arguments.workdir.absolute()
    configure_hg(clone_path)
    ensure_clone(clone_path)

    base = resolve_base(clone_path)
    if arguments.no_pull:
        logger.info("Not pulling; using the heads already in the clone.")
    else:
        pull_try_heads(clone_path, base, arguments.batch_size)

    target = resolve_merge_target(clone_path, base)

    heads = capture_heads(clone_path, target)
    if not heads:
        logger.info("No heads left to merge. Nothing to do.")
        return 0

    merged, tip = merge_heads(clone_path, target, heads)
    if not merged or tip is None:
        logger.warning("No heads were merged, so there is nothing to push.")
        return 0

    record_merge_tip(clone_path, tip)
    report_push_command(clone_path, tip)

    return 0


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "workdir",
        metavar="WORKDIR",
        type=pathlib.Path,
        help="Directory the clone lives in. Created if it does not exist.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Heads to request per pull (default: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--no-pull",
        action="store_true",
        help="Merge the heads already in the clone, fetching nothing.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log every `hg` command that is run.",
    )

    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    """Send log records to stderr, including `hg` commands when verbose."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        stream=sys.stderr,
    )


def configure_hg(clone_path: pathlib.Path) -> None:
    """Point `hg` at a configuration we control, for us and every child.

    Extensions from the operator's own hgrc interfere with bulk pulling, so
    everything reads a generated file holding just the commit identity. The
    clone's own `.hg/hgrc` still applies.
    """
    hgrc = hgrc_path(clone_path)
    if not hgrc.exists():
        # Read the username before `HGRCPATH` is set, while the operator's own
        # configuration is still in effect.
        hgrc.write_text(
            "# Generated by merge_try_heads.py. Holds only the identity used\n"
            "# to author merge commits.\n"
            "[ui]\n"
            f"username = {resolve_username()}\n"
        )
        logger.info("Wrote %s.", hgrc)

    logger.info("Running hg with the configuration at %s.", hgrc)
    os.environ["HGRCPATH"] = str(hgrc)


def hgrc_path(clone_path: pathlib.Path) -> pathlib.Path:
    """Return the generated hgrc that every `hg` invocation reads."""
    return clone_path.parent / f"{clone_path.name}.hgrc"


def state_path(clone_path: pathlib.Path, filename: str) -> pathlib.Path:
    """Return the path of one of our state files, creating its directory.

    The files live under the clone's `.hg` directory so that they are never
    reported as untracked files in the repository.
    """
    directory = clone_path / ".hg" / STATE_DIRNAME
    directory.mkdir(exist_ok=True)

    return directory / filename


def resolve_username() -> str:
    """Return the operator's Mercurial username, or `DEFAULT_USERNAME` if unset.

    An unattended run has no one to prompt, so a missing `ui.username` falls
    back to a default rather than failing.
    """
    result = subprocess.run(
        ["hg", "config", "ui.username"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    username = result.stdout.strip()
    if not username:
        logger.warning(
            "No Mercurial username is configured, so the merge commits will be "
            "authored by `%s`. Set `ui.username` in your hgrc to change that.",
            DEFAULT_USERNAME,
        )

        return DEFAULT_USERNAME

    return username


def ensure_clone(clone_path: pathlib.Path) -> None:
    """Create the seed clone, or refresh an existing one."""
    if is_mercurial_repo(clone_path):
        logger.info("Reusing the existing clone at %s.", clone_path)
        run_with_retries(
            lambda: run_hg(["pull", CLONE_URL], cwd=clone_path),
            "Pulling the seed repository",
            CLONE_ATTEMPTS,
        )
        return

    if clone_path.exists() and any(clone_path.iterdir()):
        logger.error(
            "%s is not empty and is not a Mercurial repository. Refusing to "
            "clone over it; remove it or pick another directory.",
            clone_path,
        )
        raise SystemExit(1)

    logger.info("Cloning %s into %s. This will take a while.", CLONE_URL, clone_path)
    run_with_retries(
        lambda: clone_seed(clone_path),
        "Cloning the seed repository",
        CLONE_ATTEMPTS,
    )


def is_mercurial_repo(path: pathlib.Path) -> bool:
    """Return whether `path` holds a complete Mercurial clone."""
    if not (path / ".hg").is_dir():
        return False

    # An interrupted clone can leave a `.hg` directory that Mercurial opens
    # happily but that holds no changesets.
    result = subprocess.run(
        ["hg", "--cwd", str(path), "log", "-r", "tip", "-T", "{node}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip() != NULL_NODE:
        return True

    logger.error(
        "%s holds an incomplete Mercurial clone, likely from an interrupted "
        "run. Remove it and try again.",
        path,
    )
    raise SystemExit(1)


def clone_seed(clone_path: pathlib.Path) -> None:
    """Clone the seed repository, without a working directory.

    A plain clone takes the advertised clone bundle, which is a static file the
    CDN serves well. Asking for a stream clone instead produces one very long
    response, which is what fails on Try.
    """
    run_hg(["clone", "-U", CLONE_URL, str(clone_path)])


def fetch_try_nodes(revset: str) -> List[str]:
    """Return the nodes matching a revset, from Try's `json-log` endpoint."""
    query = urllib.parse.urlencode({"rev": revset, "revcount": JSON_LOG_REVCOUNT})
    url = f"{TRY_URL}/json-log?{query}"

    logger.info("Querying Try for `%s`.", revset)
    with urllib.request.urlopen(url, timeout=JSON_LOG_TIMEOUT) as response:
        payload = json.load(response)

    return [entry["node"] for entry in payload.get("entries", [])]


def pull_try_heads(clone_path: pathlib.Path, base: str, batch_size: int) -> None:
    """Pull Try's heads into the clone, a batch of revisions at a time."""
    heads = fetch_try_nodes(HEADS_REVSET)
    logger.info("Try has %d heads.", len(heads))

    wanted = [base] + [head for head in heads if head != base]
    missing = missing_revisions(wanted, local_draft_nodes(clone_path) | {base})
    logger.info(
        "%d of %d revisions are not in the local clone yet.", len(missing), len(wanted)
    )
    if not missing:
        return

    batches = list(batched(missing, batch_size))
    logger.info(
        "Pulling %d revisions from %s in %d batches of %d.",
        len(missing),
        TRY_URL,
        len(batches),
        batch_size,
    )
    started = time.monotonic()
    deferred = []

    for count, batch in enumerate(batches, 1):
        if stop_request.requested:
            logger.warning("Stopped after %d of %d batches.", count - 1, len(batches))
            break

        if not try_pull(clone_path, batch):
            # The batch size is fixed, so a batch that will not go through is
            # set aside rather than broken up. Every run works out afresh what
            # the clone is missing, so a later run asks for these again.
            deferred += batch
            logger.warning(
                "Deferring %d revisions after %d failed attempts.",
                len(batch),
                PULL_ATTEMPTS,
            )

        report_progress(count, len(batches), started, unit="batches")

    record_deferred(clone_path, deferred)


def record_deferred(clone_path: pathlib.Path, deferred: List[str]) -> None:
    """Write the revisions a later run should retry, or clear a stale list."""
    deferred_file = state_path(clone_path, DEFERRED_FILENAME)
    if deferred:
        deferred_file.write_text("".join(f"{node}\n" for node in deferred))
        logger.warning(
            "%d revisions were deferred and are listed in %s. Run again to "
            "retry them.",
            len(deferred),
            deferred_file,
        )
    elif deferred_file.exists():
        deferred_file.unlink()
        logger.info("Nothing was deferred; removed %s.", deferred_file)


def local_draft_nodes(clone_path: pathlib.Path) -> Set[str]:
    """Return the non-public nodes already in the clone.

    Heads pulled from Try arrive as drafts and the seed publishes everything it
    ships, so one query answers which of Try's heads we already have. Asking
    per node would mean tens of thousands of `hg` invocations.
    """
    output = run_hg_output(["log", "-r", "not public()", "-T", "{node}\n"], clone_path)

    return set(output.split())


def missing_revisions(wanted: List[str], already_local: Set[str]) -> List[str]:
    """Return the wanted revisions that are not already in the clone."""
    return [node for node in wanted if node not in already_local]


def batched(items: List[str], size: int) -> Iterator[List[str]]:
    """Yield consecutive batches of at most `size` items.

    `itertools.batched` does exactly this, but it landed in Python 3.12 while
    this repository still supports 3.9.
    """
    for start in range(0, len(items), size):
        yield items[start : start + size]


def try_pull(clone_path: pathlib.Path, batch: List[str]) -> bool:
    """Attempt one pull, returning whether it succeeded."""
    command = ["pull", "--quiet", TRY_URL]
    for node in batch:
        command += ["--rev", node]

    try:
        run_with_retries(
            lambda: run_hg(command, cwd=clone_path),
            f"Pulling {len(batch)} revisions from Try",
            PULL_ATTEMPTS,
        )
        return True
    except subprocess.CalledProcessError:
        if stop_request.requested:
            raise

        return False


def capture_heads(clone_path: pathlib.Path, target: str) -> List[str]:
    """Return the nodes of the Try heads still to merge, oldest first."""
    # Heads already folded into `target` are its ancestors, so excluding them
    # is what makes a resumed run pick up where it stopped.
    revset = f"({HEADS_REVSET}) and not ancestors({target})"
    heads = run_hg_output(["log", "-r", revset, "-T", "{node}\n"], clone_path).split()

    heads_file = state_path(clone_path, HEADS_FILENAME)
    heads_file.write_text("".join(f"{head}\n" for head in heads))
    logger.info("Found %d heads to merge. Wrote them to %s.", len(heads), heads_file)

    return heads


def resolve_base(clone_path: pathlib.Path) -> str:
    """Return the revision the heads are merged into.

    The seed repository publishes a `central` bookmark at the `mozilla-central`
    tip, which is what the manual procedure merges into.
    """
    nodes = run_hg_output(
        ["log", "-r", BASE_REVSET, "-T", "{node}\n"], clone_path
    ).split()

    if len(nodes) != 1:
        logger.error(
            "`%s` resolved to %d revisions in the clone; expected exactly 1.",
            BASE_REVSET,
            len(nodes),
        )
        raise SystemExit(1)

    logger.info("Merging heads into %s.", nodes[0][:12])

    return nodes[0]


def resolve_merge_target(clone_path: pathlib.Path, base: str) -> str:
    """Return the revision to merge into, resuming an earlier run if it left one."""
    tip_file = state_path(clone_path, MERGE_TIP_FILENAME)
    if not tip_file.exists():
        return base

    node = tip_file.read_text().strip()
    if not node or not revision_exists(clone_path, node):
        logger.warning(
            "Ignoring %s, which does not name a revision in this clone.", tip_file
        )
        return base

    logger.info("Resuming from merge tip %s left by an earlier run.", node[:12])

    return node


def revision_exists(clone_path: pathlib.Path, node: str) -> bool:
    """Return whether `node` is present in the clone."""
    result = subprocess.run(
        ["hg", "--cwd", str(clone_path), "log", "-r", node, "-T", "{node}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


def merge_heads(
    clone_path: pathlib.Path, target: str, heads: List[str]
) -> Tuple[int, Optional[str]]:
    """Run the merge helper, following the commits it reports.

    Returns the number of heads merged and the node of the newest merge.
    """
    command = [
        sys.executable,
        str(MERGE_HELPER),
        target,
        str(state_path(clone_path, HEADS_FILENAME)),
    ]
    logger.info("Merging %d heads. Press Ctrl-C to stop early.", len(heads))
    started = time.monotonic()
    merged = 0
    tip = None
    asked_to_stop = False

    process = subprocess.Popen(
        command, cwd=clone_path, stdout=subprocess.PIPE, text=True
    )
    for line in process.stdout or []:
        merged, tip = parse_progress(line)

        if merged % PROGRESS_INTERVAL == 0 or merged == len(heads):
            report_progress(merged, len(heads), started)

        if stop_request.requested and not asked_to_stop:
            process.terminate()
            asked_to_stop = True

    returncode = process.wait()
    if returncode != 0 and not stop_request.requested:
        raise subprocess.CalledProcessError(returncode, command)

    if merged < len(heads):
        logger.warning("Stopped after merging %d of %d heads.", merged, len(heads))

    return merged, tip


def parse_progress(line: str) -> Tuple[int, str]:
    """Return the merge count and node from a line of merge helper output."""
    count, node = line.split()

    return int(count), node


def record_merge_tip(clone_path: pathlib.Path, tip: str) -> None:
    """Record the newest merge commit so a later run can resume from it."""
    state_path(clone_path, MERGE_TIP_FILENAME).write_text(f"{tip}\n")


def report_push_command(clone_path: pathlib.Path, tip: str) -> None:
    """Print the push command on a line of its own, ready to be copied.

    It is printed rather than logged so that no timestamp or log level shares
    the line, and it carries `HGRCPATH` because the push needs the same
    configuration the merges were made with.
    """
    logger.info("The merges are ready. To push them, run the command below.")
    print(
        f"HGRCPATH={hgrc_path(clone_path)} hg -R {clone_path} "
        f"push -r {tip} {TRY_PUSH_URL}"
    )


def report_progress(
    count: int, total: int, started: float, unit: str = "heads"
) -> None:
    """Log how far a phase has progressed and how long it has left."""
    elapsed = time.monotonic() - started
    remaining = (elapsed / count) * (total - count)
    logger.info(
        "Done %d/%d %s in %s. About %s remaining.",
        count,
        total,
        unit,
        format_duration(elapsed),
        format_duration(remaining),
    )


def format_duration(seconds: float) -> str:
    """Render a number of seconds as `HhMMm` or `MmSSs`."""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}h{minutes:02d}m"

    return f"{minutes}m{seconds:02d}s"


def run_with_retries(
    operation: Callable[[], Any], description: str, attempts: int
) -> Any:
    """Run `operation`, retrying with exponential backoff until it succeeds."""
    delays = list(backoff_delays(attempts, BASE_DELAY, MAX_DELAY))

    for attempt, delay in enumerate(delays + [None], 1):
        try:
            return operation()
        except subprocess.CalledProcessError as exc:
            if stop_request.requested:
                logger.warning("%s was interrupted by a stop request.", description)
                raise

            if delay is None:
                logger.error("%s failed after %d attempts.", description, attempts)
                raise

            logger.warning(
                "%s failed on attempt %d/%d (exit %d). Retrying in %s.",
                description,
                attempt,
                attempts,
                exc.returncode,
                format_duration(delay),
            )
            time.sleep(delay)


def backoff_delays(
    attempts: int, base_delay: float, max_delay: float
) -> Iterator[float]:
    """Yield the delay to wait before each retry, doubling up to `max_delay`."""
    for attempt in range(max(attempts - 1, 0)):
        yield min(base_delay * (2**attempt), max_delay)


def run_hg(command: List[str], cwd: Optional[pathlib.Path] = None) -> None:
    """Run an `hg` command, raising `CalledProcessError` if it fails."""
    logger.debug("Running `hg %s`.", " ".join(command))
    subprocess.run(["hg"] + command, cwd=cwd, check=True)


def run_hg_output(command: List[str], cwd: Optional[pathlib.Path] = None) -> str:
    """Run an `hg` command and return its standard output."""
    logger.debug("Running `hg %s`.", " ".join(command))
    result = subprocess.run(
        ["hg"] + command, cwd=cwd, check=True, stdout=subprocess.PIPE, text=True
    )

    return result.stdout


def run() -> int:
    """Run `main`, turning expected failures into clean error messages."""
    try:
        return main()
    except subprocess.CalledProcessError as exc:
        logger.error(
            "`%s` failed with exit status %d.", " ".join(exc.cmd), exc.returncode
        )
        return 1
    except KeyboardInterrupt:
        logger.warning(
            "Aborted. The merges already committed are kept, so re-run against "
            "the same working directory to resume."
        )
        return 130


if __name__ == "__main__":
    sys.exit(run())
