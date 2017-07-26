Test pushing an outstanding change preserves executable bits.

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > push-to-try = $TESTDIR/hgext/push-to-try
  > [push-to-try]
  > nodate = true
  > [defaults]
  > diff = --nodate
  > EOF

  $ hg init remote

  $ hg clone remote local
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd local
  $ echo line1 > file1.txt
  $ echo line1 > file2.txt
  $ chmod 755 file2.txt
  $ hg add file1.txt
  $ hg commit -m "file1.txt added"
  $ hg add file2.txt
  $ hg diff
  diff -r 153ffc71bd76 file2.txt
  --- /dev/null
  +++ b/file2.txt
  @@ -0,0 +1,1 @@
  +line1
  $ hg push-to-try -m 'try: syntax' -s ../remote
  Creating temporary commit for remote...
  A file2.txt
  pushing to ../remote
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  push complete
  temporary commit removed, repository restored

  $ hg diff
  diff -r 153ffc71bd76 file2.txt
  --- /dev/null
  +++ b/file2.txt
  @@ -0,0 +1,1 @@
  +line1

  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 1 changesets, 1 total revisions

Test the uncommited changes made it to our remote (with the right bits set).

  $ cd ../remote
  $ hg log
  changeset:   1:74dc2c45917c
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     try: syntax
  
  changeset:   0:153ffc71bd76
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     file1.txt added
  


  $ hg up -r 1
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg diff -r 0
  diff -r 153ffc71bd76 file2.txt
  --- /dev/null
  +++ b/file2.txt
  @@ -0,0 +1,1 @@
  +line1

  $ if [ -x file2.txt ]; then echo "executable"; fi
  executable
