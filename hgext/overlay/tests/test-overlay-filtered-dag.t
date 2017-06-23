  $ . $TESTDIR/hgext/overlay/tests/helpers.sh

  $ hg init empty
  $ hg -R empty serve -d --pid-file hg.pid -p $HGPORT
  $ cat hg.pid >> $DAEMON_PIDS

  $ hg init repo0
  $ cd repo0
  $ echo 0 > foo
  $ hg -q commit -A -m initial
  $ echo 1 > foo
  $ hg commit -m 'head 1 commit 1'
  $ echo 2 > foo
  $ hg commit -m 'head 1 commit 2'
  $ echo 3 > foo
  $ hg commit -m 'head 1 commit 3 FILTERED'
  $ echo 4 > foo
  $ hg commit -m 'head 1 commit 4'
  $ hg log -G -T '{node|short} {desc}'
  @  eebf284459b0 head 1 commit 4
  |
  o  6dfe620a17bb head 1 commit 3 FILTERED
  |
  o  38627e51950d head 1 commit 2
  |
  o  eb87a779cc67 head 1 commit 1
  |
  o  af1e0a150cd4 initial
  

  $ hg serve -d --pid-file hg.pid -p $HGPORT1
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ hg init dest
  $ cd dest

A non-contiguous dag range will fail to overlay.
  $ hg overlay http://localhost:$HGPORT1 'not keyword("FILTERED")' --into prefix
  pulling http://localhost:$HGPORT1 into $TESTTMP/dest/.hg/localhost~3a* (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 5 changes to 1 files
  abort: source revisions must be part of contiguous DAG range
  [255]

Passing --noncontiguous should allow a non-contiguous dag range where some of
the commits have been filtered.
  $ hg overlay http://localhost:$HGPORT1 'not keyword("FILTERED")' --into prefix --noncontiguous
  af1e0a150cd4 -> 8e52bf8e668a: initial
  eb87a779cc67 -> 452dcbcc9fb9: head 1 commit 1
  38627e51950d -> ccc09fef5c59: head 1 commit 2
  eebf284459b0 -> ed781cf9ab85: head 1 commit 4

Incremental conversion with --noncontiguous works

  $ cd ../repo0
  $ echo 5 > foo
  $ hg commit -m 'head 1 commit 5 FILTERED'
  $ echo 6 > foo
  $ hg commit -m 'head 1 commit 6'

  $ cd ../dest

  $ hg -q up tip

  $ echo 5 > prefix/foo
  $ hg commit -m 'out of band change simulating commit 5'

  $ hg overlay http://localhost:$HGPORT1 'not desc("FILTERED")' --into prefix
  pulling http://localhost:$HGPORT1 into $TESTTMP/dest/.hg/localhost~3a20123
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  abort: source revisions must be part of contiguous DAG range
  [255]

  $ hg overlay http://localhost:$HGPORT1 'not desc("FILTERED")' --into prefix --noncontiguous
  eebf284459b0 already processed as ed781cf9ab85; skipping 4/5 revisions
  8c4d7f24662e -> ee4ce23b43ca: head 1 commit 6

