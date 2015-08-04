  $ mkdir integration
  $ hg init integration/mozilla-inbound
  $ cat >> integration/mozilla-inbound/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.push_printurls = python:mozhghooks.push_printurls.hook
  > 
  > [hgmo]
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
    https://hg.mozilla.org/integration/mozilla-inbound/rev/3d7d3272d708
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=mozilla-inbound&revision=3d7d3272d708

Pushing a changeset to Try prints Treeherder URLs

  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  View your change here:
    https://hg.mozilla.org/try/rev/3d7d3272d708
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try&revision=3d7d3272d708

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
    https://hg.mozilla.org/try/rev/083142255559
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try&revision=083142255559
  
  It looks like this try push has talos jobs. Compare performance against a baseline revision:
    https://treeherder.mozilla.org/perf.html#/comparechooser?newProject=try&newRevision=083142255559

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
    https://hg.mozilla.org/try/rev/7d0edcba6d85
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try&revision=7d0edcba6d85

try-comm-central is also special

  $ hg push ../try-comm-central
  pushing to ../try-comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  
  View your changes here:
    https://hg.mozilla.org/try-comm-central/rev/3d7d3272d708
    https://hg.mozilla.org/try-comm-central/rev/083142255559
    https://hg.mozilla.org/try-comm-central/rev/7d0edcba6d85
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=try-comm-central&revision=7d0edcba6d85

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
    https://hg.mozilla.org/integration/mozilla-inbound/rev/083142255559
    https://hg.mozilla.org/integration/mozilla-inbound/rev/7d0edcba6d85
    https://hg.mozilla.org/integration/mozilla-inbound/rev/fef473558e05
    https://hg.mozilla.org/integration/mozilla-inbound/rev/b404b501615b
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=mozilla-inbound&revision=b404b501615b

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
    https://hg.mozilla.org/integration/mozilla-inbound/pushloghtml?changeset=78d884a7fbe7
  
  Follow the progress of your build on Treeherder:
    https://treeherder.mozilla.org/#/jobs?repo=mozilla-inbound&revision=78d884a7fbe7

