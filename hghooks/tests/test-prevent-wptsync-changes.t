  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init integration/autoland
  $ configurehooks integration/autoland
  $ touch integration/autoland/.hg/IS_FIREFOX_REPO
  $ hg -q clone integration/autoland client
  $ cd client
  $ mkdir -p testing/web-platform/tests
  $ mkdir testing/web-platform/meta
  $ mkdir other

Regular user can push changes both in and beyond testing/web-platform

  $ touch file0
  $ touch other/file1
  $ touch testing/web-platform/mozxbuild
  $ touch testing/web-platform/meta/file3
  $ touch testing/web-platform/tests/file4
  $ hg -q commit -A -m initial
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/integration/autoland
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
  pushing to $TESTTMP/integration/autoland
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************** ERROR *******************
  wptsync@mozilla.com can only make changes to
  the following paths on integration/autoland:
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
  pushing to $TESTTMP/integration/autoland
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************** ERROR *******************
  wptsync@mozilla.com can only make changes to
  the following paths on integration/autoland:
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

Test legal changes for wptsync user on autoland

  $ cd ..
  $ rm -rf client
  $ hg -q clone integration/autoland client
  $ cd client

wptsync user can push changes to testing/web-platform/moz.build

  $ touch testing/web-platform/moz.build
  $ hg -q commit -A -m initial
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/integration/autoland
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
  pushing to $TESTTMP/integration/autoland
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files

Test pushes to try

  $ cd ..
  $ rm -rf client
  $ hg init try
  $ configurehooks try
  $ touch try/.hg/IS_FIREFOX_REPO
  $ cat >> try/.hg/hgrc << EOF
  > [phases]
  > publish = false
  > EOF
  $ hg -q clone try client
  $ cd client
  $ mkdir -p testing/web-platform/tests
  $ mkdir testing/web-platform/meta
  $ mkdir -p taskcluster/ci
  $ mkdir other


wptsync user can push changes beyond testing/web-platform on try

  $ touch try_task_config.json
  $ touch taskcluster/ci/config.yml
  $ touch other/file1a
  $ touch testing/web-platform/moz_build
  $ touch testing/web-platform/meta/file3a
  $ touch testing/web-platform/tests/file4a
  $ hg -q commit -A -m mix-of-changes
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 6 changes to 6 files

wptsync user can push changes to testing/web-platform/moz.build on try

  $ touch testing/web-platform/moz.build
  $ hg -q commit -A -m initial
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

wptsync user can push changes to testing/web-platform/tests and meta on try

  $ touch testing/web-platform/tests/test1
  $ touch testing/web-platform/meta/meta1
  $ hg -q commit -A -m initial
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files

Test pushes outside of integration/autoland or try

  $ cd ..
  $ rm -rf client
  $ hg init server
  $ configurehooks server
  $ touch server/.hg/IS_FIREFOX_REPO
  $ hg -q clone server client
  $ cd client

Regular user can push changes to a repo other than autoland or try

  $ touch file0
  $ hg -q commit -A -m initial
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

wptsync user cannot push changes to a repo other than autoland or try

  $ touch file1
  $ hg -q commit -A -m add-a-file 
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ***************** ERROR *****************
  wptsync@mozilla.com cannot push to server
  *****************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Test pushes to a non-Firefox repo

  $ cd ..
  $ rm -rf client
  $ hg init non-firefox-repo
  $ configurehooks non-firefox-repo
  $ hg -q clone non-firefox-repo client
  $ cd client

Regular user can push changes to a non-Firefox repo

  $ touch file0
  $ hg -q commit -A -m initial
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/non-firefox-repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

wptsync user cannot push wpt changes to any non-Firefox repo

  $ mkdir -p testing/web-platform/tests 
  $ touch testing/web-platform/tests/file1
  $ hg -q commit -A -m add-a-wpt-file 
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/non-firefox-repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ********************** ERROR **********************
  wptsync@mozilla.com cannot push to non-firefox-repo
  ***************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

wptsync user cannot push changes to any non-Firefox repo

  $ touch file1
  $ hg -q commit -A -m add-a-file 
  $ USER=wptsync@mozilla.com hg push
  pushing to $TESTTMP/non-firefox-repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ********************** ERROR **********************
  wptsync@mozilla.com cannot push to non-firefox-repo
  ***************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

