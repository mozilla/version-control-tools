  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurepushlog server

  $ hg init client
  $ cd client

  $ touch foo
  $ hg -q commit -A -m initial

We set AUTOLAND_REQUEST_USER here but it should only used if the push is
performed by the AUTOLAND_USER, LANDING_WORKER_USER, or LANDING_WORKER_USER_DEV.

  $ export LANDING_WORKER_USER=lando_landing_worker@mozilla.com
  $ export LANDING_WORKER_USER_DEV=lando_landing_worker_dev@mozilla.com
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
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)

AUTOLAND_REQUEST_USER is only used for the pushuser if the user is the
autoland user or the landing worker user.

  $ echo autoland > foo
  $ hg commit -m 'autoland'
  $ USER=$AUTOLAND_USER hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  autoland or landing worker push detected
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)
  ID: 2; user: autolandrequestuser; Date: *; Rev: 1; Node: 6cce86f0aeb7e26325de47bb83f18377deb5c741 (glob)

  $ echo hello world > foo
  $ hg commit -m 'landing worker'
  $ USER=$LANDING_WORKER_USER hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  autoland or landing worker push detected
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)
  ID: 2; user: autolandrequestuser; Date: *; Rev: 1; Node: 6cce86f0aeb7e26325de47bb83f18377deb5c741 (glob)
  ID: 3; user: autolandrequestuser; Date: *; Rev: 2; Node: 2ea22efe949df1eaec2cfefa8322a394f1bb3c8d (glob)

  $ echo hello again world > foo
  $ hg commit -m 'landing worker dev'
  $ USER=$LANDING_WORKER_USER_DEV hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  autoland or landing worker push detected
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)
  ID: 2; user: autolandrequestuser; Date: *; Rev: 1; Node: 6cce86f0aeb7e26325de47bb83f18377deb5c741 (glob)
  ID: 3; user: autolandrequestuser; Date: *; Rev: 2; Node: 2ea22efe949df1eaec2cfefa8322a394f1bb3c8d (glob)
  ID: 4; user: autolandrequestuser; Date: *; Rev: 3; Node: cce08fa09941b3f978b3bcca182ebbdb8f120b94 (glob)

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
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files

  $ echo local1 > foo
  $ hg commit -m 'local prefix'

  $ USER=localuser hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 1 changesets with 1 changes to 1 files

  $ dumppushlog server
  ID: 1; user: remoteuser; Date: *; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (glob)
  ID: 2; user: autolandrequestuser; Date: *; Rev: 1; Node: 6cce86f0aeb7e26325de47bb83f18377deb5c741 (glob)
  ID: 3; user: autolandrequestuser; Date: *; Rev: 2; Node: 2ea22efe949df1eaec2cfefa8322a394f1bb3c8d (glob)
  ID: 4; user: autolandrequestuser; Date: *; Rev: 3; Node: cce08fa09941b3f978b3bcca182ebbdb8f120b94 (glob)
  ID: 5; user: remote:remoteuser; Date: *; Rev: 4; Node: f820777a860c4cce3d98a51e09b15e345b52d230 (glob)
  ID: 6; user: local:localuser; Date: *; Rev: 5; Node: 3a31c5bd57b89259cc5da60cf5743a8681ffe9fc (glob)
