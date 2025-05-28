#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv

Create repository and user

  $ hgmo create-repo mozilla-central scm_level_3
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

Set up local clone

  $ hg clone ${HGWEB_0_URL}mozilla-central
  destination directory: mozilla-central
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial

Pushing via http:// says pushing isn't allowed

  $ hg push ${HGWEB_0_URL}mozilla-central
  pushing to http://$DOCKER_HOSTNAME:*/mozilla-central (glob)
  searching for changes
  abort: authorization failed
  [255]

Pushing via ssh:// works

  $ hg push ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Blackbox logging recorded appropriate entries

  $ hgmo exec hgssh cat /repo/hg/mozilla/mozilla-central/.hg/blackbox.log
  * root @0000000000000000000000000000000000000000 (*)> init /repo/hg/mozilla/mozilla-central exited 0 after * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> -R /repo/hg/mozilla/mozilla-central serve --stdio (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *: BEGIN_SSH_SESSION mozilla-central user1@example.com (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* BEGIN_SSH_COMMAND hello (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* BEGIN_SSH_COMMAND between (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *: BEGIN_SSH_COMMAND protocaps (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* BEGIN_SSH_COMMAND batch (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* BEGIN_SSH_COMMAND listkeys (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* BEGIN_SSH_COMMAND listkeys (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* BEGIN_SSH_COMMAND unbundle (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-pretxnopen: hgext_vcsreplicator.pretxnopenhook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-prechangegroup: hgext_readonly.prechangegrouphook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> mozhooks.pretxnchangegroup.prevent_subrepos took * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> mozhooks.pretxnchangegroup.prevent_symlinks took * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> mozhooks.pretxnchangegroup.repolocked_check took * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> mozhooks.pretxnchangegroup.single_root took * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-pretxnchangegroup: hgext_mozhooks.pretxnchangegroup finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-pretxnchangegroup: hgext_pushlog.pretxnchangegrouphook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-pretxnchangegroup: hgext_vcsreplicator.pretxnchangegrouphook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> writing .hg/cache/tags2-served with 0 tags (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> writing .hg/cache/tags2 with 0 tags (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-pretxnclose: mozhghooks.populate_caches.hook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-pretxnclose: hgext_mozhooks.pretxnclose finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-pretxnclose: hgext_vcsreplicator.pretxnclosehook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> updated branch cache (base) in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> wrote branch cache (base) with 1 labels and 1 nodes (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-txnclose: hgext_vcsreplicator.txnclosehook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> exthook-changegroup.a_recordlogs: /var/hg/version-control-tools/scripts/record-pushes.sh finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-changegroup: mozhghooks.push_printurls.hook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> mozhooks.changegroup.advertise_upgrade took * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-changegroup: hgext_mozhooks.changegroup finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> pythonhook-changegroup: hgext_vcsreplicator.changegrouphook finished in * seconds (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> 1 incoming changes - new heads: 77538e1ce4be (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* BEGIN_SSH_COMMAND listkeys (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *:* END_SSH_COMMAND * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> *: END_SSH_SESSION * * (glob)
  * user1@example.com @0000000000000000000000000000000000000000 (*)> -R /repo/hg/mozilla/mozilla-central serve --stdio exited 0 after * seconds (glob)

It got replicated to mirrors

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-rev/77538e1ce4be
  200
  
  {
  "node": "77538e1ce4bec5f7aac58a7ceca2da0e38e90a72",
  "date": [0.0, 0],
  "desc": "initial",
  "backedoutby": "",
  "branch": "default",
  "bookmarks": [],
  "tags": ["tip"],
  "user": "Test User \u003csomeone@example.com\u003e",
  "parents": [],
  "children": [],
  "files": [{
  "file": "foo",
  "status": "added"
  }],
  "diff": [{
  "blockno": 1,
  "lines": [{
  "t": "",
  "n": 1,
  "l": "new file mode 100644\n"
  }]
  }],
  "phase": "public",
  "pushid": 1,
  "pushdate": [*, 0], (glob)
  "pushuser": "user1@example.com",
  "landingsystem": null,
  "git_commit": null
  }

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ http --no-headers ${HGWEB_1_URL}mozilla-central/json-rev/77538e1ce4be
  200
  
  {
  "node": "77538e1ce4bec5f7aac58a7ceca2da0e38e90a72",
  "date": [0.0, 0],
  "desc": "initial",
  "backedoutby": "",
  "branch": "default",
  "bookmarks": [],
  "tags": ["tip"],
  "user": "Test User \u003csomeone@example.com\u003e",
  "parents": [],
  "children": [],
  "files": [{
  "file": "foo",
  "status": "added"
  }],
  "diff": [{
  "blockno": 1,
  "lines": [{
  "t": "",
  "n": 1,
  "l": "new file mode 100644\n"
  }]
  }],
  "phase": "public",
  "pushid": 1,
  "pushdate": [*, 0], (glob)
  "pushuser": "user1@example.com",
  "landingsystem": null,
  "git_commit": null
  }

Pushlog should be replicated

  $ http --no-headers ${HGWEB_0_URL}mozilla-central/json-pushes
  200
  
  {"1": {"changesets": ["77538e1ce4bec5f7aac58a7ceca2da0e38e90a72"], "date": *, "git_changesets": [null], "user": "user1@example.com"}} (glob)

Upgrade notice is advertised to clients not running bundle2

  $ echo upgrade > foo
  $ hg commit -m 'upgrade notice'
  $ hg --config devel.legacy.exchange=bundle1 push ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/425a9d45c43d833916e3c803300ba4488374ac0e
  remote: 
  remote: *************************************** WARNING ****************************************
  remote: YOU ARE PUSHING WITH AN OUT OF DATE MERCURIAL CLIENT!
  remote: 
  remote: Newer versions are faster and have numerous bug fixes.
  remote: Upgrade instructions are at the following URL:
  remote: https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmozilla/installing.html
  remote: ****************************************************************************************
  remote: 
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Check logs for errors

  $ hgmo exec hgweb0 cat /var/log/httpd/hg.mozilla.org/access_log
  * - - [*/*/*:*:*:* +0000] "GET /mozilla-central?cmd=capabilities HTTP/1.1" 200 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "POST /mozilla-central?cmd=batch HTTP/1.1" 200 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "POST /mozilla-central?cmd=getbundle HTTP/1.1" 200 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "GET /mozilla-central?cmd=capabilities HTTP/1.1" 200 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "POST /mozilla-central?cmd=batch HTTP/1.1" 200 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "POST /mozilla-central?cmd=listkeys HTTP/1.1" 200 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "POST /mozilla-central?cmd=listkeys HTTP/1.1" 200 - "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "POST /mozilla-central?cmd=unbundle HTTP/1.1" 401 * "-" "mercurial/proto-1.0 (Mercurial *)" (glob)
  * - - [*/*/*:*:*:* +0000] "GET /mozilla-central/json-rev/77538e1ce4be HTTP/1.1" 200 * "-" "-" (glob)
  * - - [*/*/*:*:*:* +0000] "GET /mozilla-central/json-pushes HTTP/1.1" 200 * "-" "-" (glob)
  $ hgmo exec hgweb0 cat /var/log/httpd/hg.mozilla.org/error_log

Cleanup

  $ hgmo clean
