# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Tests for the pure helpers in `merge_try_heads`."""

import pathlib
import subprocess

import pytest

import merge_try_heads


@pytest.fixture(autouse=True)
def reset_stop_request():
    """Keep the module level stop request from leaking between tests."""
    merge_try_heads.stop_request.requested = False
    yield
    merge_try_heads.stop_request.requested = False


def install_fake_pull(monkeypatch, bad_nodes=()):
    """Make `run_hg` fail for any pull whose revisions include a bad node.

    Returns the list of revision groups each pull asked for.
    """
    bad_nodes = set(bad_nodes)
    pulled = []

    def fake_run_hg(command, cwd=None):
        nodes = [
            command[index + 1] for index, arg in enumerate(command) if arg == "--rev"
        ]
        pulled.append(nodes)
        if bad_nodes.intersection(nodes):
            raise subprocess.CalledProcessError(255, command)

    monkeypatch.setattr(merge_try_heads, "run_hg", fake_run_hg)
    monkeypatch.setattr(merge_try_heads.time, "sleep", lambda seconds: None)

    return pulled


def test_a_second_signal_aborts_instead_of_asking_again():
    stop = merge_try_heads.StopRequest()

    stop.handle_signal(2, None)

    assert stop.requested, "The first signal should ask for a graceful stop."
    with pytest.raises(KeyboardInterrupt):
        stop.handle_signal(2, None)


def test_try_pull_requests_every_revision_in_the_batch(monkeypatch):
    pulled = install_fake_pull(monkeypatch)

    assert merge_try_heads.try_pull(
        None, ["a", "b", "c"]
    ), "A batch the server accepts should report success."
    assert pulled == [
        ["a", "b", "c"]
    ], "Every revision in the batch should be requested in one pull."


def test_try_pull_reports_failure_rather_than_raising(monkeypatch):
    install_fake_pull(monkeypatch, ["c"])

    assert not merge_try_heads.try_pull(
        None, ["a", "b", "c"]
    ), "A failing batch should be reported, not raised, so it can be deferred."


def test_try_pull_propagates_a_stop_request(monkeypatch):
    install_fake_pull(monkeypatch, ["c"])
    merge_try_heads.stop_request.requested = True

    with pytest.raises(subprocess.CalledProcessError):
        merge_try_heads.try_pull(None, ["c"])


def test_missing_revisions_keeps_order_and_drops_present_nodes():
    assert merge_try_heads.missing_revisions(
        ["aaa", "bbb", "ccc", "ddd"], {"bbb", "ddd"}
    ) == [
        "aaa",
        "ccc",
    ], "Only revisions absent from the clone should be pulled, in the given order."


def test_batched_covers_every_item_exactly_once():
    heads = [f"node{index}" for index in range(101)]

    batches = list(merge_try_heads.batched(heads, 25))

    assert [len(batch) for batch in batches] == [
        25,
        25,
        25,
        25,
        1,
    ], "Batches should be full until the last one, which takes the remainder."
    assert [
        head for batch in batches for head in batch
    ] == heads, "Batching must cover every head exactly once, in order."


def test_backoff_delays_double_up_to_the_maximum():
    assert list(merge_try_heads.backoff_delays(6, 10.0, 50.0)) == [
        10.0,
        20.0,
        40.0,
        50.0,
        50.0,
    ], "Delays should double from `base_delay` and then clamp to `max_delay`."


def test_run_with_retries_retries_until_the_operation_succeeds(monkeypatch):
    slept = []
    monkeypatch.setattr(merge_try_heads.time, "sleep", slept.append)
    attempts = []

    def operation():
        attempts.append(True)
        if len(attempts) < 3:
            raise subprocess.CalledProcessError(255, ["hg", "pull"])
        return "pulled"

    merge_try_heads.run_with_retries(operation, "Pulling", 5)

    assert len(attempts) == 3, "The operation should be retried until it succeeds."
    assert slept == [15.0, 30.0], "Each retry should wait for the backoff delay."


def test_run_with_retries_reraises_after_exhausting_attempts(monkeypatch):
    monkeypatch.setattr(merge_try_heads.time, "sleep", lambda seconds: None)
    attempts = []

    def operation():
        attempts.append(True)
        raise subprocess.CalledProcessError(255, ["hg", "pull"])

    with pytest.raises(subprocess.CalledProcessError):
        merge_try_heads.run_with_retries(operation, "Pulling", 3)

    assert len(attempts) == 3, "The operation should be attempted `attempts` times."


def test_run_with_retries_does_not_retry_after_a_stop_request(monkeypatch):
    monkeypatch.setattr(merge_try_heads.time, "sleep", fail_on_sleep)
    merge_try_heads.stop_request.requested = True
    attempts = []

    def operation():
        attempts.append(True)
        raise subprocess.CalledProcessError(255, ["hg", "pull"])

    with pytest.raises(subprocess.CalledProcessError):
        merge_try_heads.run_with_retries(operation, "Pulling", 5)

    assert len(attempts) == 1, "A pending stop should prevent any further attempts."


def test_state_files_live_inside_the_clones_hg_directory(tmp_path):
    (tmp_path / ".hg").mkdir()

    path = merge_try_heads.state_path(tmp_path, merge_try_heads.HEADS_FILENAME)

    assert (
        path == tmp_path / ".hg" / "merge-try-heads" / "heads"
    ), "State files belong under `.hg` so they are never untracked files."
    assert path.parent.is_dir(), "The state directory should be created on demand."


def test_resolve_base_exits_non_zero_when_the_base_is_ambiguous(monkeypatch):
    monkeypatch.setattr(
        merge_try_heads, "run_hg_output", lambda command, cwd=None: "aaa\nbbb\n"
    )

    with pytest.raises(SystemExit) as raised:
        merge_try_heads.resolve_base(pathlib.Path("/nonexistent"))

    assert raised.value.code == 1, "A base that is not one revision should exit 1."


def test_resolve_username_uses_the_configured_username(monkeypatch):
    install_fake_hg_config(monkeypatch, "Someone <someone@example.com>\n")

    assert (
        merge_try_heads.resolve_username() == "Someone <someone@example.com>"
    ), "A configured `ui.username` should be used as it stands."


def test_resolve_username_falls_back_to_the_default(monkeypatch):
    install_fake_hg_config(monkeypatch, "")

    assert (
        merge_try_heads.resolve_username() == merge_try_heads.DEFAULT_USERNAME
    ), "An unset `ui.username` should yield the default, so a cron run can go on."


def test_the_push_command_is_printed_on_a_line_of_its_own(capsys, tmp_path):
    clone_path = tmp_path / "try-merge"

    merge_try_heads.report_push_command(clone_path, "abc123")

    assert capsys.readouterr().out.splitlines() == [
        f"HGRCPATH={tmp_path / 'try-merge.hgrc'} hg -R {clone_path} "
        f"push -r abc123 {merge_try_heads.TRY_PUSH_URL}"
    ], "The push command should be printed whole, on one line, with `HGRCPATH`."


def install_fake_hg_config(monkeypatch, stdout):
    """Make `hg config` report `stdout` instead of reading a real hgrc."""
    monkeypatch.setattr(
        merge_try_heads.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=stdout),
    )


def fail_on_sleep(delay):
    """Fail the calling test if the code under test tries to sleep."""
    raise AssertionError(f"`time.sleep({delay})` should not have been called.")
