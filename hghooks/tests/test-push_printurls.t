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
  added 1 changesets with 1 changes to 1 files
  
  View your change here:
    https://hg.mozilla.org/integration/mozilla-inbound/rev/3d7d3272d708dbf56dab75764495a40032014e3c
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=mozilla-inbound&revision=3d7d3272d708dbf56dab75764495a40032014e3c

Pushing a changeset to Try prints Treeherder URLs

  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  View your change here:
    https://hg.mozilla.org/try/rev/3d7d3272d708dbf56dab75764495a40032014e3c
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try&revision=3d7d3272d708dbf56dab75764495a40032014e3c

Pushing a changeset to Try with talos jobs prints a link to perfherder...

  $ echo '1' > foo
  $ hg commit -m 'try: -t all'
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  View your change here:
    https://hg.mozilla.org/try/rev/083142255559ec6a2b4f78157c1ea522e6fd9722
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try&revision=083142255559ec6a2b4f78157c1ea522e6fd9722
  
  It looks like this try push has talos jobs. Compare performance against a baseline revision:
    https://treeherder.mozilla.org/perf.html#/comparechooser?newProject=try&newRevision=083142255559ec6a2b4f78157c1ea522e6fd9722

and doesn't when it doesn't

  $ echo '2' > foo
  $ hg commit -m 'try: -t none'
  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  View your change here:
    https://hg.mozilla.org/try/rev/7d0edcba6d851680f3cc8730ca2e32f5fb8177a7
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try&revision=7d0edcba6d851680f3cc8730ca2e32f5fb8177a7

try-comm-central is also special

  $ hg push ../try-comm-central
  pushing to ../try-comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  
  View your changes here:
    https://hg.mozilla.org/try-comm-central/rev/3d7d3272d708dbf56dab75764495a40032014e3c
    https://hg.mozilla.org/try-comm-central/rev/083142255559ec6a2b4f78157c1ea522e6fd9722
    https://hg.mozilla.org/try-comm-central/rev/7d0edcba6d851680f3cc8730ca2e32f5fb8177a7
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try-comm-central&revision=7d0edcba6d851680f3cc8730ca2e32f5fb8177a7

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
  added 4 changesets with 4 changes to 1 files
  
  View your changes here:
    https://hg.mozilla.org/integration/mozilla-inbound/rev/083142255559ec6a2b4f78157c1ea522e6fd9722
    https://hg.mozilla.org/integration/mozilla-inbound/rev/7d0edcba6d851680f3cc8730ca2e32f5fb8177a7
    https://hg.mozilla.org/integration/mozilla-inbound/rev/fef473558e05d4b3b6dfc7019b483a2654a7ef83
    https://hg.mozilla.org/integration/mozilla-inbound/rev/b404b501615bd72a0bfbb905e636c2f1fcf110da
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=mozilla-inbound&revision=b404b501615bd72a0bfbb905e636c2f1fcf110da

Push a lot of changesets to a non-try repo

  $ for i in $(seq 0 20); do echo $i > foo; hg commit -m $i; done
  $ hg push ../integration/mozilla-inbound
  pushing to ../integration/mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 21 changesets with 21 changes to 1 files
  
  View the pushlog for these changes here:
    https://hg.mozilla.org/integration/mozilla-inbound/pushloghtml?changeset=78d884a7fbe7948375d29b261a92a948dea508db
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=mozilla-inbound&revision=78d884a7fbe7948375d29b261a92a948dea508db

