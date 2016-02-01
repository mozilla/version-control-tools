#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Create repository and user

  $ hgmo create-repo mozilla-central 3
  (recorded repository creation in replication log)
  $ hgmo create-ldap-user user1@example.com user1 1500 'User 1' --scm-level 3 --key-file user1
  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = ssh -F `pwd`/ssh_config -i `pwd`/user1 -l user1@example.com
  > EOF

Needed so hgweb_dir refreshes.
TODO we should fix this in hgweb_dir or a hack of hgweb_dir, support for
this is in Mercurial 3.6
  $ sleep 1

Pushing a commit to a repo works

  $ hg clone ${HGWEB_0_URL}mozilla-central
  destination directory: mozilla-central
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4be
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Blackbox logging recorded appropriate entries

  $ hgmo exec hgssh cat /repo/hg/mozilla/mozilla-central/.hg/blackbox.log
  * user1@example.com (*)> serve --stdio (glob)
  * user1@example.com (*)> pythonhook-pretxnopen: hgext_vcsreplicator.pretxnopenhook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-prechangegroup: hgext_readonly.prechangegrouphook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-pretxnchangegroup: mozhghooks.single_root.hook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-pretxnchangegroup: hgext_pushlog.pretxnchangegrouphook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-pretxnchangegroup: hgext_vcsreplicator.pretxnchangegrouphook finished in * seconds (glob)
  * user1@example.com (*)> updated base branch cache in * seconds (glob)
  * user1@example.com (*)> wrote base branch cache with 1 labels and 1 nodes (glob)
  * user1@example.com (*)> pythonhook-prepushkey: hgext_readonly.prepushkeyhook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-pretxnclose: hgext_vcsreplicator.pretxnclosehook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-pushkey: hgext_vcsreplicator.pushkeyhook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-txnclose: hgext_vcsreplicator.txnclosehook finished in * seconds (glob)
  * user1@example.com (*)> exthook-changegroup.a_recordlogs: /repo/hg/scripts/record-pushes.sh finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-changegroup: mozhghooks.push_printurls.hook finished in * seconds (glob)
  * user1@example.com (*)> pythonhook-changegroup: hgext_vcsreplicator.changegrouphook finished in * seconds (glob)
  * user1@example.com (*)> 1 incoming changes - new heads: 77538e1ce4be (glob)
  * user1@example.com (*)> -R /repo/hg/mozilla/mozilla-central serve --stdio exited 0 after * seconds (glob)

It got replicated to mirrors

  $ hgmo exec hgweb0 /repo/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-rev/77538e1ce4be
  200
  
  {
  "node": "77538e1ce4bec5f7aac58a7ceca2da0e38e90a72",
  "date": [0.0, 0],
  "desc": "initial",
  "branch": "default",
  "bookmarks": [],
  "tags": ["tip"],
  "user": "Test User \u003csomeone@example.com\u003e",
  "parents": [],
  "phase": "public"
  }

  $ http --no-headers ${HGWEB_1_URL}mozilla-central/json-rev/77538e1ce4be
  200
  
  {
  "node": "77538e1ce4bec5f7aac58a7ceca2da0e38e90a72",
  "date": [0.0, 0],
  "desc": "initial",
  "branch": "default",
  "bookmarks": [],
  "tags": ["tip"],
  "user": "Test User \u003csomeone@example.com\u003e",
  "parents": [],
  "phase": "public"
  }

Pushlog should be replicated

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-pushes
  200
  
  {"1": {"changesets": ["77538e1ce4bec5f7aac58a7ceca2da0e38e90a72"], "date": *, "user": "user1@example.com"}} (glob)

Upgrade notice is advertised to clients not running bundle2

  $ echo upgrade > foo
  $ hg commit -m 'upgrade notice'
  $ hg --config experimental.bundle2-exp=false push ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/425a9d45c43d
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Cleanup

  $ hgmo clean
