#require docker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Create repository and user

  $ hgmo create-repo mozilla-central 3
  $ hgmo create-ldap-user user1@example.com user1 1500 'User 1' --scm-level 3 --key-file user1
  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = ssh -F `pwd`/ssh_config -i `pwd`/user1 -l user1@example.com
  > EOF

Needed so hgweb_dir refreshes.
TODO we should fix this in hgweb_dir or a hack of hgweb_dir
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
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: replication to mirrors completed successfully in \d+.\ds (re)
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/96ee1d7354c4

It got replicated to mirrors

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-rev/96ee1d7354c4
  200
  
  {
  "node": "96ee1d7354c4ad7372047672c36a1f561e3a6a4c",
  "date": [0.0, 0],
  "desc": "initial",
  "branch": "default",
  "bookmarks": [],
  "tags": ["tip"],
  "user": "test",
  "parents": [],
  "phase": "public"
  }

  $ http --no-headers ${HGWEB_1_URL}mozilla-central/json-rev/96ee1d7354c4
  200
  
  {
  "node": "96ee1d7354c4ad7372047672c36a1f561e3a6a4c",
  "date": [0.0, 0],
  "desc": "initial",
  "branch": "default",
  "bookmarks": [],
  "tags": ["tip"],
  "user": "test",
  "parents": [],
  "phase": "public"
  }

Pushlog should be replicated

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-pushes
  200
  
  {"1": {"changesets": ["96ee1d7354c4ad7372047672c36a1f561e3a6a4c"], "date": *, "user": "user1@example.com"}} (glob)

  $ hgmo stop
