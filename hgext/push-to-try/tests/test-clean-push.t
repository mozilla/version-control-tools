Test pushing with no outstanding change works.

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
  $ hg add file1.txt
  $ hg commit -m "file1.txt added"

  $ hg push-to-try -m 'try: syntax' -s ../remote
  Creating temporary commit for remote...
  pushing to ../remote
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 1 files
  push complete
  temporary commit removed, repository restored

  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 1 changesets, 1 total revisions

Test try commit made it to our remote.

  $ cd ../remote
  $ hg log
  changeset:   1:c5fa4c037d42
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     try: syntax
  
  changeset:   0:153ffc71bd76
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     file1.txt added
  

  $ hg up -r 1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg diff -r 0
