  $ hg init mozilla-inbound
  $ cat >> mozilla-inbound/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.push_printurls = python:mozhghooks.push_printurls.hook
  > EOF

  $ hg init try
  $ cp mozilla-inbound/.hg/hgrc try/.hg/hgrc

  $ hg init try-comm-central
  $ cp mozilla-inbound/.hg/hgrc try-comm-central/.hg/hgrc

  $ hg init unknown
  $ cp mozilla-inbound/.hg/hgrc unknown/.hg/hgrc

Push a single changeset to a non-try repo print the URL

  $ hg init client
  $ cd client
  $ touch foo
  $ hg commit -A -m 'Bug 123 - Add foo'
  adding foo
  $ hg push ../mozilla-inbound
  pushing to ../mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  You can view your change at the following URL:
    https://hg.mozilla.org/integration/mozilla-inbound/rev/3d7d3272d708

Pushing to a non-tree repo does nothing

  $ hg push ../unknown
  pushing to ../unknown
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Pushing a changeset to Try prints Treeherder and TBPL URLs

  $ hg push ../try
  pushing to ../try
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  You can view your change at the following URL:
    https://hg.mozilla.org/try/rev/3d7d3272d708
  You can view the progress of your build at the following URL:
    https://treeherder.mozilla.org/#/jobs?repo=try&revision=3d7d3272d708
  Alternatively, view them on TBPL (soon to be deprecated):
    https://tbpl.mozilla.org/?tree=Try&rev=3d7d3272d708

try-comm-central is also special

  $ hg push ../try-comm-central
  pushing to ../try-comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  You can view your change at the following URL:
    https://hg.mozilla.org/try-comm-central/rev/3d7d3272d708
  You can view the progress of your build at the following URL:
    https://treeherder.mozilla.org/#/jobs?repo=try-comm-central&revision=3d7d3272d708
  Alternatively, view them on TBPL (soon to be deprecated):
    https://tbpl.mozilla.org/?tree=Thunderbird-Try&rev=3d7d3272d708

Push multiple changesets to a non-try repo

  $ echo '1' > foo
  $ hg commit -m '1'
  $ echo '2' > foo
  $ hg commit -m '2'
  $ hg push ../mozilla-inbound
  pushing to ../mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  You can view your changes at the following URLs:
    https://hg.mozilla.org/integration/mozilla-inbound/rev/3129f8f30e80
    https://hg.mozilla.org/integration/mozilla-inbound/rev/e046d8987087

Push a lot of changesets to a non-try repo

  $ for i in $(seq 0 20); do echo $i > foo; hg commit -m $i; done
  $ hg push ../mozilla-inbound
  pushing to ../mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 21 changesets with 21 changes to 1 files
  You can view the pushlog for your changes at the following URL:
    https://hg.mozilla.org/integration/mozilla-inbound/pushloghtml?changeset=77380cff16a1

