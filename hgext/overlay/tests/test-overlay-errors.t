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
  $ hg commit -m 'head 1 commit 3'
  $ hg -q up -r 0
  $ echo 4 > foo
  $ hg commit -m 'head 2 commit 1'
  created new head
  $ echo 5 > foo
  $ hg commit -m 'head 2 commit 2'
  $ hg merge -t :local 3
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg commit -m 'merge 3 into 5'
  $ hg log -G -T '{node|short} {desc}'
  @    775588bbd687 merge 3 into 5
  |\
  | o  ac6bba5999bc head 2 commit 2
  | |
  | o  09ef50e3bf32 head 2 commit 1
  | |
  o |  5272c3c4ef03 head 1 commit 3
  | |
  o |  38627e51950d head 1 commit 2
  | |
  o |  eb87a779cc67 head 1 commit 1
  |/
  o  af1e0a150cd4 initial
  

  $ hg serve -d --pid-file hg.pid -p $HGPORT1
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ hg init dest

--into required

  $ cd dest
  $ hg overlay http://localhost:$HGPORT
  abort: --into must be specified
  [255]

Local repos not accepted

  $ hg overlay ../empty --into prefix
  abort: source repo cannot be local
  [255]

No revisions is an error

  $ hg overlay http://localhost:$HGPORT --into prefix
  abort: unable to determine source revisions
  [255]

Non-contiguous revision range is an error

  $ hg overlay http://localhost:$HGPORT1 'af1e0a150cd4 + ac6bba5999bc' --into prefix
  pulling http://localhost:$HGPORT1 into $TESTTMP/dest/.hg/localhost~3a* (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 7 changesets with 7 changes to 1 files
  new changesets af1e0a150cd4:775588bbd687 (?)
  abort: source revisions must be part of contiguous DAG range
  [255]

Multiple heads is an error

  $ hg overlay http://localhost:$HGPORT1 '::5272c3c4ef03 + ::ac6bba5999bc' --into prefix
  abort: source revisions must be part of same DAG head
  [255]

Cannot overlay merges

  $ hg overlay http://localhost:$HGPORT1 --into prefix
  abort: do not support overlaying merges: 775588bbd687
  [255]

Dest revision is invalid

  $ hg overlay --dest foo http://localhost:$HGPORT1 af1e0a150cd4::tip --into prefix
  abort: unknown revision 'foo'!
  [255]
