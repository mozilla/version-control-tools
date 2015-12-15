#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Create repository and user

  $ hgmo create-repo mozilla-central 1
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central

Pushing works as expected

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: replication of phases data completed successfully in *s (glob)
  remote: replication of changegroup data completed successfully in *s (glob)
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4be

Marking individual repo as read-only works

  $ echo readonly > foo
  $ hg commit -m readonly
  $ hgmo exec hgssh touch /repo/hg/mozilla/mozilla-central/.hg/readonlyreason
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: repository is read only
  remote: refusing to add changesets
  abort: prechangegroup.readonly hook failed
  [255]

  $ hgmo exec hgssh rm -f /repo/hg/mozilla/mozilla-central/.hg/readonlyreason

Global read only file works

  $ hgmo exec hgssh touch /etc/mercurial/readonlyreason
  $ hg push
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: all repositories currently read only
  remote: refusing to add changesets
  abort: prechangegroup.readonly hook failed
  [255]

  $ hgmo clean
