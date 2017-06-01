  $ . $TESTDIR/hgext/overlay/tests/helpers.sh

  $ hg init source
  $ cd source
  $ mkdir dir0
  $ echo dir0/file0 > dir0/file0
  $ echo dir0/file1 > dir0/file1
  $ hg -q commit -A -m 'add dir0/file0 and dir0/file1'
  $ mkdir dir1
  $ echo dir1/file0 > dir1/file0
  $ hg -q commit -A -m 'add dir1/file0' -u 'Another User <another@example.com>'
  $ hg serve -d --pid-file hg.pid -p $HGPORT
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd ..

  $ hg init dest
  $ cd dest
  $ echo foo > foo
  $ hg -q commit -A -m initial
  $ hg -q up null

  $ hg overlay http://localhost:$HGPORT --into subdir 'user("another@example.com")'
  pulling http://localhost:$HGPORT into $TESTTMP/dest/.hg/localhost~3a* (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 3 changes to 3 files
  3b2a19679264 -> e9b986f72c98: add dir1/file0

  $ hg log -p --debug
  changeset:   1:e9b986f72c9857034d84cef7f1348a93afcb1c4e
  tag:         tip
  phase:       draft
  parent:      0:21e2edf037c2267b7c1d7a038d64bca58d5caa59
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    1:177de7a23eaa5f26e7c8e97f0c6be3a07dbc3e6e
  user:        Another User <another@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  files+:      subdir/dir1/file0
  extra:       branch=default
  extra:       subtree_revision=3b2a1967926470d5fbfdcdadca4ef639e2bbee94
  extra:       subtree_source=https://example.com/repo
  description:
  add dir1/file0
  
  
  diff --git a/subdir/dir1/file0 b/subdir/dir1/file0
  new file mode 100644
  --- /dev/null
  +++ b/subdir/dir1/file0
  @@ -0,0 +1,1 @@
  +dir1/file0
  
  changeset:   0:21e2edf037c2267b7c1d7a038d64bca58d5caa59
  phase:       draft
  parent:      -1:0000000000000000000000000000000000000000
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    0:9091aa5df980aea60860a2e39c95182e68d1ddec
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  files+:      foo
  extra:       branch=default
  description:
  initial
  
  
  diff --git a/foo b/foo
  new file mode 100644
  --- /dev/null
  +++ b/foo
  @@ -0,0 +1,1 @@
  +foo
  
  $ hg files -r tip
  foo
  subdir/dir1/file0
