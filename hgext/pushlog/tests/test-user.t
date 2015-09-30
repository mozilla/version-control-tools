  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurepushlog server

  $ hg init client
  $ cd client

  $ touch foo
  $ hg -q commit -A -m initial

No user environment variables result in error

  $ unset USER
  $ unset REMOTE_USER
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  authenticated user not found; refusing to write into pushlog
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.pushlog hook failed
  [255]

Empty user environment variables result in error

  $ USER= hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  authenticated user not found; refusing to write into pushlog
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.pushlog hook failed
  [255]

  $ REMOTE_USER= hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  authenticated user not found; refusing to write into pushlog
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.pushlog hook failed
  [255]

REMOTE_USER is preferred over USER

  $ REMOTE_USER=remoteuser USER=user hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)

User prefixing works

  $ cat >> ../server/.hg/hgrc << EOF
  > [pushlog]
  > userprefix = local
  > remoteuserprefix = remote
  > EOF

  $ echo remote1 > foo
  $ hg commit -m 'remote prefix'

  $ REMOTE_USER=remoteuser hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog

  $ echo local1 > foo
  $ hg commit -m 'local prefix'

  $ USER=localuser hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)
  ID: 2; user: remote:remoteuser; Date: *; Rev: 1; Node: 91efce04b0592cbdc9afbb4dd1b0268eedb0f788 (glob)
  ID: 3; user: local:localuser; Date: *; Rev: 2; Node: 19b7f3ef78c12ba31fb2d02e3262e2de8bd6aea4 (glob)
