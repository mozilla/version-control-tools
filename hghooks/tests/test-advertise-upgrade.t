  $ . $TESTDIR/hghooks/tests/common.sh

  $ hg init server
  $ configurehooks server

  $ hg -q clone --pull server client
  $ cd client

Modern hg with bundle2 doesn't see advertisement

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Old client without bundle2 does

  $ echo out-of-date > foo
  $ hg -q commit -A -m out-of-date
  $ hg push --config devel.legacy.exchange=bundle1
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  *************************************** WARNING ****************************************
  YOU ARE PUSHING WITH AN OUT OF DATE MERCURIAL CLIENT!
  
  Newer versions are faster and have numerous bug fixes.
  Upgrade instructions are at the following URL:
  https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmozilla/installing.html
  ****************************************************************************************
  

Modern hg without bundle2 gets message
(this is a bit sub-optimal, but we should never see this in the wild, so
it's acceptable)

  $ echo bundle2disabled > foo
  $ hg commit -m 'bundle2 disabled'
  $ hg --config devel.legacy.exchange=bundle1 push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  *************************************** WARNING ****************************************
  YOU ARE PUSHING WITH AN OUT OF DATE MERCURIAL CLIENT!
  
  Newer versions are faster and have numerous bug fixes.
  Upgrade instructions are at the following URL:
  https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmozilla/installing.html
  ****************************************************************************************
  
