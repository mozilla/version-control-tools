#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ standarduser

Enable the firefoxtree extension on the consumer side. This simulates a
consumer that would strip Firefox tree bookmarks during pulls when pulling
from a server that advertises the firefoxtrees capability.

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

Create the repository and process the init message.

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central

Mark the consumer's local repo as a Firefox repo. Without the fix, firefoxtree
would strip Firefox tree bookmarks (e.g. "central") when pulling from a server
that advertises the firefoxtrees capability.

  $ touch $TESTTMP/repos/mozilla-central/.hg/IS_FIREFOX_REPO

Configure the server repo to advertise the firefoxtrees capability by enabling
the firefoxtree extension with servetags=True and marking it as a Firefox repo.

  $ hgmo exec hgssh touch /repo/hg/mozilla/mozilla-central/.hg/IS_FIREFOX_REPO
  $ hgmo exec hgssh /set-hgrc-option mozilla-central extensions firefoxtree /var/hg/version-control-tools/hgext/firefoxtree
  $ hgmo exec hgssh /set-hgrc-option mozilla-central firefoxtree servetags True

Push a commit with a Firefox tree bookmark. Because txnclosehook skips pushkey
messages when a changegroup is present, the bookmark is not replicated via a
separate pushkey message: the consumer must pick it up during the pull.

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg bookmark central
  $ hg push -B central
  pushing to ssh://*:$HGPORT/mozilla-central (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d\.\d+s (re)
  exporting bookmark central

The consumer pull command sets firefoxtree.replication=true, which disables
bookmark filtering in the firefoxtree extension. The "central" bookmark is
preserved even though firefoxtree is loaded and the server advertises the
firefoxtrees capability.

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['77538e1ce4be']) from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 --config=firefoxtree.replication=true -- ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > adding remote bookmark central
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 77538e1ce4be
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/mozilla-central, heads: ['77538e1ce4be'], last_push_id: 1) from partition 2 offset 4

The central bookmark is preserved despite firefoxtree being loaded.

  $ hg -R $TESTTMP/repos/mozilla-central bookmarks
     central                   0:77538e1ce4be

Cleanup

  $ hgmo clean
