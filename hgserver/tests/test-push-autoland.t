#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Create repository and user

  $ export AUTOLAND_REQUEST_USER="autolandrequester@example.com"
  $ hgmo create-repo mozilla-central 3
  $ hgmo create-ldap-user bind-autoland@mozilla.com user1 1500 'Otto Land' --scm-level 3 --key-file autoland
  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = ssh -o "SendEnv AUTOLAND_REQUEST_USER" -F `pwd`/ssh_config -i `pwd`/autoland -l bind-autoland@mozilla.com
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
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: autoland push detected
  remote: recorded push in pushlog
  remote: replication of phases data completed successfully in \d+.\ds (re)
  remote: replication of changegroup data completed successfully in \d+.\ds (re)
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4be

Pushlog should be replicated

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-pushes
  200
  
  {"1": {"changesets": ["77538e1ce4bec5f7aac58a7ceca2da0e38e90a72"], "date": *, "user": "autolandrequester@example.com"}} (glob)

Cleanup

  $ hgmo clean
