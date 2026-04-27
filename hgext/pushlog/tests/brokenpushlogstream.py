# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Test extension that replaces the `pushlog-stream` wireproto command
with one whose behaviour is controlled by a file on disk.

Used by `test-pull-stream-errors.t` to exercise the client-side error
and retry paths in `exchangepullpushlog` without requiring real
transport-level failures.

The file `.hg/pushlog-stream-fail-mode` on the server selects the
failure mode for the next request. Supported modes:

  always-error
      Yield an `error <...>` trailer immediately. No data rows.

  always-error-after-one
      Yield one data row, then an `error <...>` trailer.

  always-truncate
      Yield one data row, then close the stream without any trailer.

Anything else (including an empty or missing file) falls through to
the normal streaming behaviour with an `ok` trailer.
"""

from mercurial import (
    pycompat,
    wireprototypes,
    wireprotov1server as wireproto,
)


MODE_FILE = b"pushlog-stream-fail-mode"


def current_mode(repo):
    return repo.vfs.tryread(MODE_FILE).strip()


def broken_pushlog_stream(repo, proto, firstpush):
    mode = current_mode(repo)

    def generate():
        try:
            firstpush_int = int(firstpush)

            if mode == b"always-error":
                yield b"error simulated server error\n"
                return

            pushes_iter = iter(repo.pushlog.pushes(start_id=firstpush_int))
            try:
                pushid, who, when, nodes = next(pushes_iter)
                yield b"%d %s %d %s\n" % (
                    pushid,
                    who,
                    when,
                    b" ".join(nodes),
                )
            except StopIteration:
                # No pushes to stream — fall through; any trailing
                # branches below will still behave according to mode.
                pass

            if mode == b"always-error-after-one":
                yield b"error simulated error after one row\n"
                return

            if mode == b"always-truncate":
                # No trailer — simulate a truncated response.
                return

            for pushid, who, when, nodes in pushes_iter:
                yield b"%d %s %d %s\n" % (
                    pushid,
                    who,
                    when,
                    b" ".join(nodes),
                )
            yield b"ok\n"
        except Exception as exc:
            message = pycompat.bytestr(exc).replace(b"\n", b" ")
            yield b"error %s\n" % message

    return wireprototypes.streamreslegacy(gen=generate())


def extsetup(ui):
    transports = {
        key
        for key, value in wireprototypes.TRANSPORTS.items()
        if value[b"version"] == 1
    }
    wireproto.commands[b"pushlog-stream"] = wireprototypes.commandentry(
        broken_pushlog_stream,
        args=b"firstpush",
        transports=transports,
        permission=b"pull",
    )
