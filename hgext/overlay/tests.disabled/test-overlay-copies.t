  $ . $TESTDIR/hgext/overlay/tests/helpers.sh

  $ hg init source
  $ cd source
  $ echo content > file-original
  $ hg -q commit -A -m 'add file-original'
  $ hg cp file-original file-copy
  $ hg commit -A -m 'copy to file-copy'
  $ hg mv file-original file-renamed
  $ hg commit -m 'rename file-original to file-renamed'
  $ hg serve -d --pid-file hg.pid -p $HGPORT
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd ..

  $ hg init dest
  $ cd dest
  $ echo foo > foo
  $ hg -q commit -A -m initial
  $ hg -q up null

  $ hg overlay http://localhost:$HGPORT --into overlayed
  pulling http://localhost:$HGPORT into $TESTTMP/dest/.hg/localhost~3a* (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 3 files
  new changesets 6e554f89d70b:120fa44d9d88 (?)
  6e554f89d70b -> b7adb4318010: add file-original
  abfabb8b7304 -> fb3553af8eea: copy to file-copy
  120fa44d9d88 -> 5159eec60fc8: rename file-original to file-renamed

  $ hg log -p
  changeset:   3:5159eec60fc8
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     rename file-original to file-renamed
  
  diff --git a/overlayed/file-original b/overlayed/file-renamed
  rename from overlayed/file-original
  rename to overlayed/file-renamed
  
  changeset:   2:fb3553af8eea
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     copy to file-copy
  
  diff --git a/overlayed/file-original b/overlayed/file-copy
  copy from overlayed/file-original
  copy to overlayed/file-copy
  
  changeset:   1:b7adb4318010
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     add file-original
  
  diff --git a/overlayed/file-original b/overlayed/file-original
  new file mode 100644
  --- /dev/null
  +++ b/overlayed/file-original
  @@ -0,0 +1,1 @@
  +content
  
  changeset:   0:21e2edf037c2
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial
  
  diff --git a/foo b/foo
  new file mode 100644
  --- /dev/null
  +++ b/foo
  @@ -0,0 +1,1 @@
  +foo
  
