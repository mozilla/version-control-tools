  $ . $TESTDIR/hghooks/tests/common.sh

  $ mkdir integration
  $ hg init integration/mozilla-inbound
  $ configurehooks integration/mozilla-inbound
  $ cat >> integration/mozilla-inbound/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.push_printurls = python:mozhghooks.push_printurls.hook
  > 
  > [mozilla]
  > repo_root = $TESTTMP
  > EOF

  $ hg init try
  $ cp integration/mozilla-inbound/.hg/hgrc try/.hg/hgrc
  $ cat >> try/.hg/hgrc << EOF
  > [mozilla]
  > treeherder_repo = try
  > EOF

  $ hg init try-comm-central
  $ cp integration/mozilla-inbound/.hg/hgrc try-comm-central/.hg/hgrc
  $ cat >> try-comm-central/.hg/hgrc << EOF
  > [mozilla]
  > treeherder_repo = try-comm-central
  > EOF

  $ cat >> integration/mozilla-inbound/.hg/hgrc << EOF
  > [mozilla]
  > treeherder_repo = mozilla-inbound
  > EOF

Push a single changeset to a non-try repo print the URL

  $ hg init client
  $ cd client
  $ touch foo
  $ hg commit -A -m 'Bug 123 - Add foo'
  adding foo
  $ hg push ../integration/mozilla-inbound
  pushing to ../integration/mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  View your change here:
    https://hg.mozilla.org/integration/mozilla-inbound/rev/3d7d3272d708dbf56dab75764495a40032014e3c
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/jobs?repo=mozilla-inbound&revision=3d7d3272d708dbf56dab75764495a40032014e3c
  added 1 changesets with 1 changes to 1 files

Pushing a changeset to Try prints Treeherder URLs

  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  View your change here:
    https://hg.mozilla.org/try/rev/3d7d3272d708dbf56dab75764495a40032014e3c
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/jobs?repo=try&revision=3d7d3272d708dbf56dab75764495a40032014e3c
  added 1 changesets with 1 changes to 1 files


try-comm-central is also special

  $ hg push ../try-comm-central
  pushing to ../try-comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  View your change here:
    https://hg.mozilla.org/try-comm-central/rev/3d7d3272d708dbf56dab75764495a40032014e3c
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/jobs?repo=try-comm-central&revision=3d7d3272d708dbf56dab75764495a40032014e3c
  added 1 changesets with 1 changes to 1 files

Push multiple changesets to a non-try repo

  $ echo '1' > foo
  $ hg commit -m '1'
  $ echo '2' > foo
  $ hg commit -m '2'
  $ hg push ../integration/mozilla-inbound
  pushing to ../integration/mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  View your changes here:
    https://hg.mozilla.org/integration/mozilla-inbound/rev/3129f8f30e8030fb70e98e1e1f5012fa766aa76d
    https://hg.mozilla.org/integration/mozilla-inbound/rev/e046d8987087573fa34c3191458d06981631f630
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/jobs?repo=mozilla-inbound&revision=e046d8987087573fa34c3191458d06981631f630
  added 2 changesets with 2 changes to 1 files

Push a lot of changesets to a non-try repo

  $ for i in $(seq 0 20); do echo $i > foo; hg commit -m $i; done
  $ hg push ../integration/mozilla-inbound
  pushing to ../integration/mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  View the pushlog for these changes here:
    https://hg.mozilla.org/integration/mozilla-inbound/pushloghtml?changeset=77380cff16a1957231435f85bad42f0e5da0719f
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/jobs?repo=mozilla-inbound&revision=77380cff16a1957231435f85bad42f0e5da0719f
  added 21 changesets with 21 changes to 1 files

