#require hgmodocker

  $ . $TESTDIR/hghooks/tests/common.sh
  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ hgmo create-repo not-mozilla-central scm_level_3
  (recorded repository creation in replication log)
  $ scm4user
  $ hg clone ssh://${SSH_SERVER}:${SSH_PORT}/not-mozilla-central client
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client

Pushing to not-mozilla-central should succeed if user has "active_scm_allow_direct_push" (scm level 4)

  $ touch foo
  $ hg commit -A -m 'a new file'
  adding foo
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/not-mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Successful push: 57a078f14741 by l4user@example.com (ACTIVE_SCM_ALLOW_DIRECT_PUSH)
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/not-mozilla-central/rev/57a078f147413eada087f5d2ace88598c06d2c42
  remote: recorded changegroup in replication log in *s (glob)


  $ cd ..
  $ scm3user
  $ hg clone ssh://${SSH_SERVER}:${SSH_PORT}/not-mozilla-central client2
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 57a078f14741
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved


  $ cd client2

Pushing to not-mozilla-central should fail if the ACTIVE_SCM_LEVEL_3 user has 
provided neither MAGIC_WORDS nor a justification in their top commit.

  $ echo closed > foo
  $ hg commit -m 'this should fail'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/not-mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: ********************************** ERROR ***********************************
  remote: Pushing directly to this repo is disallowed, please use Lando.
  remote: To override, in your head commit, include the literal string, "MANUAL PUSH:",
  remote: followed by a sentence of justification.
  remote: ****************************************************************************
  remote: 
  remote: transaction abort!
  remote: rollback completed
  remote: pretxnchangegroup.mozhooks hook failed
  abort: push failed on remote
  [255]


Pushing to not-mozilla-central should succeed if the user has ACTIVE_SCM_LEVEL_3 and
magic words with justification

  $ hg commit --amend -q -m 'PRIVILEGED PUSH: because I want to'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/not-mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: ********************************** ERROR ***********************************
  remote: Pushing directly to this repo is disallowed, please use Lando.
  remote: To override, in your head commit, include the literal string, "MANUAL PUSH:",
  remote: followed by a sentence of justification.
  remote: ****************************************************************************
  remote: 
  remote: transaction abort!
  remote: rollback completed
  remote: pretxnchangegroup.mozhooks hook failed
  abort: push failed on remote
  [255]


Pushing multiple changesets to not-mozilla-central is accepted if the user has
ACTIVE_SCM_LEVEL_3 and the magic words and justification are on the top commit.

  $ echo dummy0 > foo
  $ hg commit -m 'dummy0'
  $ echo dummy1 >> foo
  $ hg commit -m 'dummy1'
  $ echo dummy2 >> foo
  $ hg commit -m 'dummy2'
  $ echo forceit >> foo
  $ hg commit -m 'PRIVILEGED PUSH: because I can'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/not-mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 5 changesets with 5 changes to 1 files
  remote: 
  remote: ********************************** ERROR ***********************************
  remote: Pushing directly to this repo is disallowed, please use Lando.
  remote: To override, in your head commit, include the literal string, "MANUAL PUSH:",
  remote: followed by a sentence of justification.
  remote: ****************************************************************************
  remote: 
  remote: transaction abort!
  remote: rollback completed
  remote: pretxnchangegroup.mozhooks hook failed
  abort: push failed on remote
  [255]

Pushing multiple changesets to not-mozilla-central should fail if the user has
ACTIVE_SCM_LEVEL_3 and the magic words on the top commit, but justification is missing.

  $ echo dummy4 >> foo
  $ hg commit -m 'dummy4'
  $ echo dummy5 >> foo
  $ hg commit -m 'dummy5'
  $ echo "no justification" >> foo
  $ hg commit -m 'PRIVILEGED PUSH:'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/not-mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 8 changesets with 8 changes to 1 files
  remote: 
  remote: ********************************** ERROR ***********************************
  remote: Pushing directly to this repo is disallowed, please use Lando.
  remote: To override, in your head commit, include the literal string, "MANUAL PUSH:",
  remote: followed by a sentence of justification.
  remote: ****************************************************************************
  remote: 
  remote: transaction abort!
  remote: rollback completed
  remote: pretxnchangegroup.mozhooks hook failed
  abort: push failed on remote
  [255]

Pushing multiple changesets to not-mozilla-central should fail if the user has
ACTIVE_SCM_LEVEL_3 and the magic words & justification are on the wrong commit.

  $ echo dummy6 >> foo
  $ hg commit -m 'dummy6'
  $ echo "justification in wrong commit" >> foo
  $ hg commit -m 'PRIVILEGED PUSH: at least I tried'
  $ echo dummy7 >> foo
  $ hg commit -m 'dummy7'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/not-mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 11 changesets with 11 changes to 1 files
  remote: 
  remote: ********************************** ERROR ***********************************
  remote: Pushing directly to this repo is disallowed, please use Lando.
  remote: To override, in your head commit, include the literal string, "MANUAL PUSH:",
  remote: followed by a sentence of justification.
  remote: ****************************************************************************
  remote: 
  remote: transaction abort!
  remote: rollback completed
  remote: pretxnchangegroup.mozhooks hook failed
  abort: push failed on remote
  [255]

  $ hgmo clean
