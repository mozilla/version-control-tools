  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurepushlog server

  $ hg init client
  $ cd client

  $ touch foo
  $ hg -q commit -A -m initial

We set AUTOLAND_REQUEST_USER here but it should only used if the push is
performed by the AUTOLAND_USER.

  $ export AUTOLAND_USER=bind-autoland@mozilla.com
  $ export AUTOLAND_REQUEST_USER=autolandrequestuser

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

AUTOLAND_REQUEST_USER is only used for the pushuser if the user is the
autoland user

  $ echo autoland > foo
  $ hg commit -m 'autoland'
  $ USER=$AUTOLAND_USER hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  autoland push detected
  recorded push in pushlog

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)
  ID: 2; user: autolandrequestuser; Date: *; Rev: 1; Node: 6cce86f0aeb7e26325de47bb83f18377deb5c741 (glob)

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
  ID: 2; user: autolandrequestuser; Date: *; Rev: 1; Node: 6cce86f0aeb7e26325de47bb83f18377deb5c741 (glob)
  ID: 3; user: remote:remoteuser; Date: *; Rev: 2; Node: 55b4fd16322dd6b7455e7633ae3bdf165ad35af3 (glob)
  ID: 4; user: local:localuser; Date: *; Rev: 3; Node: b3c24a16cf565149ecf515256b25fc3566734b8d (glob)
