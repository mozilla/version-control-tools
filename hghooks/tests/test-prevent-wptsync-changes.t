  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurehooks server
  $ touch server/.hg/IS_FIREFOX_REPO
  $ hg -q clone server client
  $ cd client
  $ mkdir -p testing/web-platform/tests
  $ mkdir testing/web-platform/meta
  $ mkdir other

Regular user can push changes both in and out of testing/web-platform

  $ touch file0
  $ touch other/file1
  $ touch testing/web-platform/mozxbuild
  $ touch testing/web-platform/meta/file3
  $ touch testing/web-platform/tests/file4
  $ hg -q commit -A -m initial
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 5 changes to 5 files

wptsync user cannot push changes beyond testing/web-platform/tests or meta

  $ touch file0a
  $ touch other/file1a
  $ touch testing/web-platform/moz_build
  $ touch testing/web-platform/meta/file3a
  $ touch testing/web-platform/tests/file4a
  $ hg -q commit -A -m mix-of-legal-illegal-changes
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 5 changes to 5 files
  
  ****************** ERROR *******************
  wptsync@mozilla.com can only make changes to
  testing/web-platform/moz.build
  testing/web-platform/meta
  testing/web-platform/tests
  
  Illegal paths found:
  file0a
  other/file1a
  testing/web-platform/moz_build
  ********************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

wptsync user cannot push changes beyond testing/web-platform, multiple

  $ touch file1a
  $ hg -q commit -A -m illegal-changes  
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 6 changes to 6 files
  
  ****************** ERROR *******************
  wptsync@mozilla.com can only make changes to
  testing/web-platform/moz.build
  testing/web-platform/meta
  testing/web-platform/tests
  
  Illegal paths found:
  file0a
  other/file1a
  testing/web-platform/moz_build
  ********************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Test legal changes for wptsync user

  $ cd ..
  $ rm -rf client
  $ hg -q clone server client
  $ cd client

wptsync user can push changes to testing/web-platform/moz.build

  $ touch testing/web-platform/moz.build
  $ hg -q commit -A -m initial
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

wptsync user can push changes to testing/web-platform/tests and meta

  $ touch testing/web-platform/tests/test1
  $ touch testing/web-platform/meta/meta1
  $ hg -q commit -A -m initial
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
