  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.commit_message = python:mozhghooks.commit-message.hook
  > EOF

  $ hg clone server client
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mq=
  > EOF

Normal commits must have a bug number. The following tests look for the
various syntax allowed.

No bug is rejected

  $ echo 'no bug' > foo
  $ hg commit -A -m 'create foo'
  adding foo
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev b648292ceed8 needs a bug number.
  test
  create foo
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]

  $ hg strip -r .
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/b648292ceed8-backup.hg

Bug XYZ syntax is accepted

  $ echo preferred > foo
  $ hg commit -A -m 'Bug 603517 - Enable mochitest to optionally run in loops without restarting r=ctalbert'
  adding foo
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Bug #XYZ form is accepted

  $ echo poundnumber > foo
  $ hg commit -m 'Bug #123456 - add test'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

b=XYZ at beginning is accepted

  $ echo bequals > foo
  $ hg commit -m 'b=630117, rename typed array slice(); r=jwalden, a=block'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

b=XYZ in middle is accepted

  $ echo bequalsmiddle > foo
  $ hg commit -m 'ARM assembler tweaks. (b=588021, r=cdleary)'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Backouts need to reference a changeset with 12 digit hash.

Backing out a single changeset

  $ hg backout -r . -m 'Backed out changeset d9be75507e88'
  reverting foo
  changeset 4:2f75aa63ea4b backs out changeset 3:d9be75507e88
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ hg backout -r . -m 'Backout of 2f75aa63ea4b due to bustage'
  reverting foo
  changeset 5:bcdfc8c76354 backs out changeset 4:2f75aa63ea4b
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Including the local numeric ID is silly, but allowed

  $ hg backout -r . -m 'backout 5:bcdfc8c76354'
  reverting foo
  changeset 6:31f438c5b89c backs out changeset 5:bcdfc8c76354
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Checking "revert to" syntax

  $ hg backout -r . -m 'Revert to changeset bcdfc8c76354 due to incomplete backout'
  reverting foo
  changeset 7:cfff144d2d79 backs out changeset 6:31f438c5b89c
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Multiple changesets should work

  $ hg backout -r . -m 'Backout changesets  9e4ab3907b29, 3abc0dbbf710 due to m-oth permaorange'
  reverting foo
  changeset 8:427250785150 backs out changeset 7:cfff144d2d79
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Tag syntax should be allowed

  $ echo addedtag > foo
  $ hg commit -m 'Added tag AURORA_BASE_20110412 for changeset 427250785150'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

"no bug" should work around bug requirement

  $ echo nobug > foo
  $ hg commit -m 'Fix typo in comment within nsFrame.cpp (no bug) rs=dbaron'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo nobug2 > foo
  $ hg commit -m 'Fix ARM assert (no bug, r=cdleary).'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo nobugbackout > foo
  $ hg commit -m 'Backout 3b59c196aaf9 - no bug # in commit message'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Test some bad commit messages

  $ echo massrevert > foo
  $ hg commit -m 'Mass revert m-i to the last known good state'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev aceedd3a7a9c needs a bug number.
  test
  Mass revert m-i to the last known good state
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo updaterevision > foo
  $ hg commit -m 'update revision of Add-on SDK tests to latest tip; test-only'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev 28a84ef30213 needs a bug number.
  test
  update revision of Add-on SDK tests to latest tip; test-only
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo fixstupid > foo
  $ hg commit -m 'Fix stupid bug in foo::bar()'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev a76cbc1dad35 needs a bug number.
  test
  Fix stupid bug in foo::bar()
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo firstline > foo
  $ cat >> message << EOF
  > First line does not have a bug number
  > 
  > bug 123456
  > EOF
  $ hg commit -l message
  $ rm message
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev 15188c21f222 needs a bug number.
  test
  First line does not have a bug number
  
  bug 123456
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo imported1 > foo
  $ hg commit -m 'imported patch phishingfixes'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev f8ed876d3982 needs a bug number.
  test
  imported patch phishingfixes
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo imported2 > foo
  $ hg commit -m 'imported patch 441197-1'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev 2c7d6012b15a needs a bug number.
  test
  imported patch 441197-1
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo backout > foo
  $ hg commit -m "Back out Dao's push because of build bustage"
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Backout rev e9f73684e287 needs a bug number or a rev id.
  test
  Back out Dao's push because of build bustage
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo bump > foo
  $ hg commit -m 'Bump mozilla-central version numbers for the next release on a CLOSED TREE'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev 01f57b6e29c4 needs a bug number.
  test
  Bump mozilla-central version numbers for the next release on a CLOSED TREE
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo bumpsync > foo
  $ hg commit -m 'Bump Sync version to 1.9.0. r=me'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev 465821751091 needs a bug number.
  test
  Bump Sync version to 1.9.0. r=me
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]
  $ hg strip -r . > /dev/null

  $ echo try > foo
  $ hg commit -m 'checkin 1 try: -b do -p all'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  Rev 4e02cc296e91 uses try syntax. (Did you mean to push to Try instead?)
  test
  checkin 1 try: -b do -p all
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.commit_message hook failed
  [255]

IGNORE BAD COMMIT MESSAGES should work

  $ echo ignore > foo
  $ hg commit -m 'IGNORE BAD COMMIT MESSAGES'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
