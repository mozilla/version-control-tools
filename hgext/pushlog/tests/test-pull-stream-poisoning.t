Reproducer for connection-poisoning bug in `apply_pushlog_stream`.

When a pushlog stream row references a changeset the client doesn't
have, the client warns and bails out of `apply_pushlog_stream`. The
bug: it used to bail without consuming the rest of the streamed
response, leaving leftover bytes in the wireproto channel. Because
both `pushlog` and `firefoxtree` wrap `_pullobsolete` in production,
firefoxtree's wrap issues `pullop.remote._call(b"firefoxtrees")` after
pushlog returns, and that call would read the leftover pushlog rows as
its response and abort with `unexpected response`.

This test loads `postpushlogcall`, a small extension that mimics
firefoxtree's wrap shape — it issues `pullop.remote.heads()` after the
pushlog wrap finishes. Without the drain fix, the leftover bytes are
read by `heads()` and the pull aborts. With the drain fix, the stream
is consumed up to the trailer and the follow-up call succeeds.

  $ . $TESTDIR/hghooks/tests/common.sh

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > EOF

  $ export USER=hguser

Set up the server.

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ cd ..

Create the initial commit and push so the server has push 1.

  $ hg init seed
  $ cd seed
  $ touch foo
  $ hg commit -A -m 'initial'
  adding foo
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files
  $ cd ..

Clone the server over SSH so the client has push 1 and its pushlog
row.

  $ hg --config extensions.pushlog=$TESTDIR/hgext/pushlog clone ssh://user@dummy/$TESTTMP/server client
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 pushes
  added 1 changesets with 1 changes to 1 files
  new changesets 96ee1d7354c4
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Add three more pushes to the server. Push 2 is the one the client
will pull a single revision of below; pushes 3 and 4 reference
changesets the client won't have, so the pushlog stream will bail.

  $ cd seed
  $ echo foo2 > foo
  $ hg commit -m 'second'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files
  $ echo foo3 > foo
  $ hg commit -m 'third'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files
  $ echo foo4 > foo
  $ hg commit -m 'fourth'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files
  $ cd ..

Configure the client with both `pushlog` and the test extension. The
test extension wraps `_pullobsolete` last, so it runs as the outer
wrap: `orig` runs the pushlog wrap (which streams pushlog rows and may
bail), then the test extension issues a follow-up wireproto call on
the same peer.

  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > postpushlogcall = $TESTDIR/hgext/pushlog/tests/postpushlogcall.py
  > EOF

Pull just push 2's revision over SSH. The server's pushlog stream
will emit rows for pushes 2, 3, and 4 (then `ok`). Push 2's changeset
is now local, so it is recorded. Push 3's changeset is not local, so
the bail-out fires. With the drain fix, the rest of the stream
(push 4 row + `ok` trailer) is consumed before returning, leaving the
SSH channel clean for the follow-up `heads()` call.

  $ hg pull -r d0fddd3a3fb5 ssh://user@dummy/$TESTTMP/server
  pulling from ssh://user@dummy/$TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  received pushlog entry for unknown changeset 53532d3f0b038c6e7bf435c45f28c1be1ab97049; ignoring
  added 1 pushes
  added 1 changesets with 1 changes to 1 files
  new changesets d0fddd3a3fb5
  (run 'hg update' to get a working copy)

The pushlog should contain pushes 1 and 2 only — push 3 was bailed on
and push 4 was drained without being inserted.

  $ dumppushlog client
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)

  $ cd ..
