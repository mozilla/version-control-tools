  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init mozilla-unified
  $ hg init releases/mozilla-beta
  $ configurehooks releases/mozilla-beta
  $ touch releases/mozilla-beta/.hg/IS_FIREFOX_REPO
  $ hg -q clone releases/mozilla-beta client
  $ cd client
  $ mkdir -p config
  $ mkdir -p browser/config
  $ mkdir -p other

Regular user can push changes both merge day and other changes

  $ touch file0
  $ touch other/file1
  $ echo 60.0.0 > config/milestone.txt
  $ echo 60.0 > browser/config/version.txt
  $ hg -q commit -A -m initial
  $ USER=someone@example.com hg push
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 4 changes to 4 files

ffxbld-merge user cannot push non-merge day changes

  $ touch file0a
  $ touch other/file1a
  $ echo 60.1.0 > config/milestone.txt
  $ echo 60.1.0 > browser/config/version.txt
  $ hg -q commit -A -m mix-of-legal-illegal-changes
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  *************** ERROR ***************
  ffxbld-merge can only push changes to
  the following paths:
  .hgtags
  CLOBBER
  browser/config/mozconfigs/
  browser/config/version.txt
  browser/config/version_display.txt
  browser/locales/l10n-changesets.json
  build/defines.sh
  build/mozconfig.common
  config/milestone.txt
  services/sync/modules/constants.sys.js
  xpcom/components/Module.h
  
  Illegal paths found:
  file0a
  other/file1a
  *************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

ffxbld-merge user cannot push non-merge day changes, multiple

  $ touch file1a
  $ hg -q commit -A -m illegal-changes  
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  *************** ERROR ***************
  ffxbld-merge can only push changes to
  the following paths:
  .hgtags
  CLOBBER
  browser/config/mozconfigs/
  browser/config/version.txt
  browser/config/version_display.txt
  browser/locales/l10n-changesets.json
  build/defines.sh
  build/mozconfig.common
  config/milestone.txt
  services/sync/modules/constants.sys.js
  xpcom/components/Module.h
  
  Illegal paths found:
  file0a
  other/file1a
  *************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

ffxbld-merge can push changes that have been pushed to mozilla-unified

  $ USER=someone@example.com hg push $TESTTMP/mozilla-unified
  pushing to $TESTTMP/mozilla-unified
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 9 changes to 7 files
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 5 changes to 5 files

Test legal changes for ffxbld-merge user on mozilla-beta

  $ cd ..
  $ rm -rf client
  $ hg -q clone releases/mozilla-beta client
  $ cd client

ffxbld-merge user can push merge-day changes

  $ echo 60.2.0 > config/milestone.txt
  $ echo 60.2 > browser/config/version.txt
  $ hg -q commit -A -m initial
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files

ffxbld-merge user can push merges that match the first parent

  $ echo p1 > file-merge
  $ hg -q commit -A -m 'left parent'
  $ hg bookmark left
  $ hg -q update '.^'
  $ echo p2 > file-merge
  $ hg -q commit -A -m 'right parent'
  $ hg bookmark right
  $ USER=someone@example.com hg -q push --force $TESTTMP/mozilla-unified
  $ hg update -q left
  $ hg debugsetparents left right
  $ hg commit -m'left merge'
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 2 changes to 1 files

ffxbld-merge user can't push merges that don't match the first parent

  $ hg -q update right
  $ hg debugsetparents left right
  $ hg commit -m'right merge'
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************** ERROR *******************
  ffxbld-merge cannot push non-trivial merges.
  ********************************************
  
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

ffxbld-merge user cannot push merge day changes to any non-Firefox repo

  $ mkdir -p config
  $ mkdir -p browser/config
  $ echo 60.1.0 > config/milestone.txt
  $ echo 60.1.0 > browser/config/version.txt
  $ hg -q commit -A -m add-a-wpt-file 
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/non-firefox-repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR ******************************
  ffxbld-merge cannot push to non-firefox repository non-firefox-repo
  *******************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

ffxbld-merge user cannot push changes to any non-Firefox repo

  $ touch file1
  $ hg -q commit -A -m add-a-file 
  $ USER=ffxbld-merge hg push
  pushing to $TESTTMP/non-firefox-repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ****************************** ERROR ******************************
  ffxbld-merge cannot push to non-firefox repository non-firefox-repo
  *******************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]


Test tbbld-merge user

  $ cd ..
  $ rm -rf client
  $ rm -rf non-firefox-repo
  $ hg init comm-central
  $ hg init releases/comm-beta
  $ configurehooks releases/comm-beta
  $ touch releases/comm-beta/.hg/IS_THUNDERBIRD_REPO
  $ hg -q clone releases/comm-beta client
  $ cd client
  $ mkdir -p mail/config
  $ mkdir other

tbbld-merge user cannot push non-merge day changes

  $ touch file0a
  $ touch other/file1a
  $ echo 60.1.0 > mail/config/version.txt
  $ hg -q commit -A -m mix-of-legal-illegal-changes
  $ USER=tbbld-merge hg push
  pushing to $TESTTMP/releases/comm-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ************** ERROR ***************
  tbbld-merge can only push changes to
  the following paths:
  .gecko_rev.yml
  .hgtags
  mail/config/mozconfigs/
  mail/config/version.txt
  mail/config/version_display.txt
  mail/locales/l10n-changesets.json
  suite/config/version.txt
  suite/config/version_display.txt
  
  Illegal paths found:
  file0a
  other/file1a
  ************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

tbbld-merge user cannot push non-merge day changes, multiple

  $ touch file1a
  $ hg -q commit -A -m illegal-changes
  $ USER=tbbld-merge hg push
  pushing to $TESTTMP/releases/comm-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ************** ERROR ***************
  tbbld-merge can only push changes to
  the following paths:
  .gecko_rev.yml
  .hgtags
  mail/config/mozconfigs/
  mail/config/version.txt
  mail/config/version_display.txt
  mail/locales/l10n-changesets.json
  suite/config/version.txt
  suite/config/version_display.txt
  
  Illegal paths found:
  file0a
  other/file1a
  ************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]


tbbld-merge can push changes that have been pushed to comm-central

  $ USER=someone@example.com hg push $TESTTMP/comm-central
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 4 changes to 4 files
  $ USER=tbbld-merge hg push
  pushing to $TESTTMP/releases/comm-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 4 changes to 4 files

Test legal changes for tbbld-merge user on comm-beta

  $ cd ..
  $ rm -rf client
  $ hg -q clone releases/comm-beta client
  $ cd client

tbbld-merge user can push merge-day changes

  $ echo 60.2 > mail/config/version.txt
  $ hg -q commit -A -m initial
  $ USER=tbbld-merge hg push
  pushing to $TESTTMP/releases/comm-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

ffxbld-merge user cannot push change to any Thunderbird repo

  $ echo 78.7 > mail/config/version_display.txt
  $ hg -q commit -A -m ffx-change
  $ USER=ffxbld-merge hg push $TESTTMP/releases/comm-beta
  pushing to $TESTTMP/releases/comm-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ******************************* ERROR *******************************
  ffxbld-merge cannot push to non-firefox repository releases/comm-beta
  *********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]


Test pushes to a non-Thunderbird repo

  $ cd ..
  $ rm -rf client
  $ hg init non-thunderbird-repo
  $ configurehooks non-thunderbird-repo
  $ hg -q clone non-thunderbird-repo client
  $ cd client

tbbld-merge user cannot push merge day changes to any non-Thunderbird repo

  $ mkdir -p mail/config
  $ echo 78.6.0 > mail/config/version.txt
  $ hg -q commit -A -m add-a-file
  $ USER=tbbld-merge hg push
  pushing to $TESTTMP/non-thunderbird-repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ********************************* ERROR **********************************
  tbbld-merge cannot push to non-thunderbird repository non-thunderbird-repo
  **************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

tbbld-merge user cannot push changes to any non-Thunderbird repo

  $ touch file1
  $ hg -q commit -A -m add-a-file
  $ USER=tbbld-merge hg push
  pushing to $TESTTMP/non-thunderbird-repo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ********************************* ERROR **********************************
  tbbld-merge cannot push to non-thunderbird repository non-thunderbird-repo
  **************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]


Test pushes to a Firefox repo

  $ cd ..
  $ rm -rf client
  $ hg -q clone releases/mozilla-beta client
  $ cd client
  $ mkdir -p browser/config


tbbld-merge user cannot push changes to any Firefox repo

  $ echo 78.0.0 > browser/config/version.txt
  $ hg -q commit -A -m initial
  $ USER=tbbld-merge hg push $TESTTMP/releases/mozilla-beta
  pushing to $TESTTMP/releases/mozilla-beta
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ********************************** ERROR **********************************
  tbbld-merge cannot push to non-thunderbird repository releases/mozilla-beta
  ***************************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

