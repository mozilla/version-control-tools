#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

  $ hgmo create-repo mozilla-central 1
  $ standarduser

Install hooks that mimic production

  $ hgmo exec hgssh /activate-hook mozilla-central pretxnchangegroup.b_singlehead python:mozhghooks.single_head_per_branch.hook
  $ hgmo exec hgssh /activate-hook mozilla-central pretxnchangegroup.c_commitmessage python:mozhghooks.commit-message.hook
  $ hgmo exec hgssh /activate-hook mozilla-central pretxnchangegroup.d_webidl python:mozhghooks.prevent_webidl_changes.hook
  $ hgmo exec hgssh /activate-hook mozilla-central pretxnchangegroup.e_idl_no_uuid python:mozhghooks.prevent_idl_change_without_uuid_bump.hook

  $ hg -q clone ${HGWEB_0_URL}mozilla-central
  $ cd mozilla-central

Verify hooks are working by pushing something that should be rejected

  $ touch foo
  $ hg -q commit -A -m 'This is a bad commit message'
  $ hg push ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: 
  remote: ************************** ERROR ****************************
  remote: Rev ad1fb17c23be needs "Bug N" or "No bug" in the commit message.
  remote: Test User <someone@example.com>
  remote: This is a bad commit message
  remote: *************************************************************
  remote: 
  remote: 
  remote: transaction abort!
  remote: rollback completed
  abort: pretxnchangegroup.c_commitmessage hook failed
  [255]

  $ hgmo clean
