#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

Create and seed repository

  $ hgmo create-repo mozilla-central 1

  $ hg clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central > /dev/null
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push > /dev/null
  $ cd ..

Create a clonebundles manifest

  $ hgmo exec hgssh sudo -u hg /repo/hg/venv_tools/bin/python /repo/hg/version-control-tools/scripts/generate-hg-s3-bundles --no-upload mozilla-central &> /dev/null

Cloning with a client that supports clonebundles should advertise the
feature

#if hg36+

  $ hg clone -U ${HGWEB_0_URL}mozilla-central clonebundles-advertise
  requesting all changes
  remote: this server supports the experimental "clone bundles" feature that should enable faster and more reliable cloning
  remote: help test it by setting the "experimental.clonebundles" config flag to "true"
  remote: IMPORTANT: verify you are running Mercurial 3.6.1 or newer or `hg pull` will be broken if you enable the feature
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

#else

  $ hg clone -U ${HGWEB_0_URL}mozilla-central clonebundles-no-support
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

#endif

We shouldn't see the message if we attempted to use clonebundles

#if hg36+

  $ hg --config experimental.clonebundles=true --config ui.clonebundlefallback=true clone -U ${HGWEB_0_URL}mozilla-central clonebundles-no-advertise
  applying clone bundle from https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg
  HTTP error fetching bundle: HTTP Error 403: Forbidden
  falling back to normal clone
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

#endif

  $ hgmo stop
