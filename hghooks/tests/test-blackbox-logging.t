  $ . $TESTDIR/hghooks/tests/common.sh

  $ hg init server
  $ configurehooks server

  $ hg -q clone server client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Blackbox log should contain times for each of our hooks

  $ grep mozhooks $TESTTMP/server/.hg/blackbox.log
  *> mozhooks.pretxnchangegroup.prevent_subrepos took * seconds (glob)
  *> mozhooks.pretxnchangegroup.prevent_symlinks took * seconds (glob)
  *> mozhooks.pretxnchangegroup.single_root took * seconds (glob)
  *> pythonhook-pretxnchangegroup: hgext_mozhooks.pretxnchangegroup finished in * seconds (glob)
  *> mozhooks.changegroup.advertise_upgrade took * seconds (glob)
  *> pythonhook-changegroup: hgext_mozhooks.changegroup finished in * seconds (glob)
