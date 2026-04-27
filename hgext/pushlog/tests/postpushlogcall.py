# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Test extension that wraps `exchange._pullobsolete` to issue a
wireproto call after the pushlog wrap has finished.

This mimics what `firefoxtree.wrappedpullobsolete` does in production:
both extensions wrap `_pullobsolete`, and whichever loads later runs as
the outer wrap, so its post-`orig` work executes after the inner
pushlog wrap has consumed the pushlog stream.

If `apply_pushlog_stream` returns early without draining the stream,
the leftover bytes would be read as the response to the call below
and the pull would abort with `unexpected response`.
"""

from mercurial import (
    exchange,
    extensions,
)


def post_pushlog_heads_call(orig, pullop):
    res = orig(pullop)

    if not pullop.remote.local():
        # Issue a follow-up wireproto call on the same peer. With the
        # drain fix in place, this returns the remote heads cleanly;
        # without it, it would read pushlog rows and abort.
        pullop.remote.heads()

    return res


def extsetup(ui):
    extensions.wrapfunction(
        exchange, "_pullobsolete", post_pushlog_heads_call
    )
