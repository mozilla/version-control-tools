#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Create repository and user

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central

Pushing works as expected

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Marking individual repo as read-only works

  $ echo readonly > foo
  $ hg commit -m readonly
  $ hgmo exec hgssh touch /repo/hg/mozilla/mozilla-central/.hg/readonlyreason
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: repository is read only
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]

  $ hgmo exec hgssh rm -f /repo/hg/mozilla/mozilla-central/.hg/readonlyreason

Global read only file works

  $ hgmo exec hgssh touch /repo/hg/readonlyreason
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: all repositories currently read only
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]

  $ hgmo clean
