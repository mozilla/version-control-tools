#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

Create some repository and a few commits

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m "initial commit"
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/2d30fb72c11e311c32234b1c6b05a916a30aafcc
  remote: recorded changegroup in replication log in \d\.\d+s (re)

Confirm replication to hgweb hosts

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-central log
  changeset:   0:2d30fb72c11e
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial commit
  
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-central log
  changeset:   0:2d30fb72c11e
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial commit
  

Run `replicatedelete` on hgssh for mozilla-central

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatedelete
  wrote delete message into replication log
  repo deleted from local host

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag


Confirm the repos are deleted

  $ hgmo exec hgssh ls -la /repo/hg/mozilla/mozilla-central
  ls: cannot access /repo/hg/mozilla/mozilla-central: No such file or directory
  [2]
  $ hgmo exec hgweb0 ls -la /repo/hg/mozilla/mozilla-central
  ls: cannot access /repo/hg/mozilla/mozilla-central: No such file or directory
  [2]
  $ hgmo exec hgweb1 ls -la /repo/hg/mozilla/mozilla-central
  ls: cannot access /repo/hg/mozilla/mozilla-central: No such file or directory
  [2]

Set `consumer.backup=true` on a node and re-create the repos to test deletion on a backup node
 
  $ hgmo exec hgweb0 /set-config-option /etc/mercurial/vcsreplicator.ini consumer backup true
  $ hgmo exec hgweb0 supervisorctl restart vcsreplicator:2
  vcsreplicator:2: stopped
  vcsreplicator:2: started
  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/mozilla-central/rev/2d30fb72c11e311c32234b1c6b05a916a30aafcc
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatedelete
  wrote delete message into replication log
  repo deleted from local host

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

Confirm the repos are only deleted on the non-backup nodes

  $ hgmo exec hgssh ls /repo/hg/mozilla
  users
  $ hgmo exec hgweb0 ls /repo/hg/mozilla
  mozilla-central
  $ hgmo exec hgweb1 ls /repo/hg/mozilla

Output of consumer logs:

  $ hgmo exec hgweb0 tail -n 49 /var/log/vcsreplicator/consumer.log
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['2d30fb72c11e311c32234b1c6b05a916a30aafcc']) from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (2d30fb72c11e311c32234b1c6b05a916a30aafcc) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer   $ /var/hg/venv_replication/bin/hg pull -r2d30fb72c11e311c32234b1c6b05a916a30aafcc -- ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > remote: Warning: Permanently added the RSA host key for IP address '*' to the list of known hosts. (glob)
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 pushes
  vcsreplicator.consumer   > updating moz-owner file
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 2d30fb72c11e
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/mozilla-central, heads: ['2d30fb72c11e311c32234b1c6b05a916a30aafcc'], last_push_id: 1) from partition 2 offset 4
  vcsreplicator.consumer processing hg-repo-delete-1: (repo: {moz}/mozilla-central) from partition 2 offset 5
  vcsreplicator.consumer repository at /repo/hg/mozilla/mozilla-central deleted
  vcsreplicator.consumer received signal 15
  vcsreplicator.consumer exiting from main consume loop
  vcsreplicator.consumer process exiting gracefully
  vcsreplicator.consumer starting consumer for topic=pushdata group=hgweb0 partitions=[2]
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 1
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 6
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 7
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 8
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['2d30fb72c11e311c32234b1c6b05a916a30aafcc']) from partition 2 offset 9
  vcsreplicator.consumer pulling 1 heads (2d30fb72c11e311c32234b1c6b05a916a30aafcc) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer   $ /var/hg/venv_replication/bin/hg pull -r2d30fb72c11e311c32234b1c6b05a916a30aafcc -- ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 pushes
  vcsreplicator.consumer   > updating moz-owner file
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 2d30fb72c11e
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/mozilla-central, heads: ['2d30fb72c11e311c32234b1c6b05a916a30aafcc'], last_push_id: 1) from partition 2 offset 10
  vcsreplicator.consumer processing hg-repo-delete-1: (repo: {moz}/mozilla-central) from partition 2 offset 11
  vcsreplicator.consumer node is a backup; ignoring delete for /repo/hg/mozilla/mozilla-central

Clean

  $ hgmo clean
