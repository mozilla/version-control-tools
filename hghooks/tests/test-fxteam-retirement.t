  $ hg init server
  $ cat > server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.fxteam = python:mozhghooks.fxteam_retirement.hook
  > EOF

  $ hg -q clone server client
  $ cd client

Users not in the list can't push

  $ touch file0
  $ hg -q commit -A -m initial
  $ USER=someone@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  ************************************************************************
  The fx-team repository is in the process of being retired.
  
  Push access to this repository will be going away.
  
  The repository became read-only on October 19 except to
  sheriffs and people who have pushed recently. The repository
  will be read-only to everyone starting on November 1.
  
  YOU NO LONGER HAVE PUSH ACCESS TO FX-TEAM.
  
  Please land commits via MozReview+Autoland. Or, use
  mozilla-inbound (but it will be going away eventually too)
  ************************************************************************
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.fxteam hook failed
  [255]

A warning should be printed when an allowed user pushes

  $ USER=ahunt@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  ************************************************************************
  The fx-team repository is in the process of being retired.
  
  Push access to this repository will be going away.
  
  The repository became read-only on October 19 except to
  sheriffs and people who have pushed recently. The repository
  will be read-only to everyone starting on November 1.
  
  Please start changing your development workflow to base commits
  off of mozilla-central instead of fx-team.
  
  Please consider landing commits via MozReview+Autoland (preferred)
  or to mozilla-inbound. (mozilla-inbound will eventually go away too
  so use of Autoland is highly encouraged.)
  ************************************************************************

  $ touch file1
  $ hg -q commit -A -m head1
  $ USER=ahunt@mozilla.com hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  ************************************************************************
  The fx-team repository is in the process of being retired.
  
  Push access to this repository will be going away.
  
  The repository became read-only on October 19 except to
  sheriffs and people who have pushed recently. The repository
  will be read-only to everyone starting on November 1.
  
  Please start changing your development workflow to base commits
  off of mozilla-central instead of fx-team.
  
  Please consider landing commits via MozReview+Autoland (preferred)
  or to mozilla-inbound. (mozilla-inbound will eventually go away too
  so use of Autoland is highly encouraged.)
  ************************************************************************

  $ hg -q up -r 0
  $ touch file2
  $ hg -q commit -A -m head2

  $ hg merge 1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg commit -m merge

Merge on tip commit should not print message

  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 1 files
