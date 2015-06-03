Test pushing with outstanding changes that delete a file works.

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
  $ echo line2 > file2.txt
  $ hg add file1.txt
  $ hg add file2.txt
  $ hg commit -m "file1.txt and file2.txt added"
  $ hg rm file1.txt
  $ echo line3 > file2.txt

  $ hg status
  M file2.txt
  R file1.txt

  $ hg push-to-try -m 'try: syntax' -s ../remote
  The following will be pushed to ../remote:
  M file2.txt
  R file1.txt
  Creating temporary commit for remote...
  pushing to ../remote
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 3 changes to 2 files
  push complete
  temporary commit removed, repository restored

  $ hg status
  M file2.txt
  R file1.txt

  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  2 files, 1 changesets, 2 total revisions

  $ hg diff
  diff -r 61db39535340 file1.txt
  --- a/file1.txt
  +++ /dev/null
  @@ -1,1 +0,0 @@
  -line1
  diff -r 61db39535340 file2.txt
  --- a/file2.txt
  +++ b/file2.txt
  @@ -1,1 +1,1 @@
  -line2
  +line3


Test try commit made it to our remote.

  $ cd ../remote
  $ hg log
  changeset:   1:80f5f007cc2c
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     try: syntax
  
  changeset:   0:61db39535340
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     file1.txt and file2.txt added
  

  $ hg up -r 1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg diff -r 0
  diff -r 61db39535340 file1.txt
  --- a/file1.txt
  +++ /dev/null
  @@ -1,1 +0,0 @@
  -line1
  diff -r 61db39535340 file2.txt
  --- a/file2.txt
  +++ b/file2.txt
  @@ -1,1 +1,1 @@
  -line2
  +line3
