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
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
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


Output of consumer logs:

  $ hgmo exec hgweb0 tail -n 23 /var/log/vcsreplicator/consumer.log
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  vcsreplicator.consumer processing hg-repo-init-2 from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  vcsreplicator.consumer processing hg-changegroup-2 from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (2d30fb72c11e311c32234b1c6b05a916a30aafcc) and 1 nodes from ssh://hgssh/mozilla-central into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer   $ /var/hg/venv_replication/bin/hg pull -r2d30fb72c11e311c32234b1c6b05a916a30aafcc -- ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://hgssh/mozilla-central
  vcsreplicator.consumer   > remote: Warning: Permanently added the RSA host key for IP address '*' to the list of known hosts. (glob)
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > added 1 pushes
  vcsreplicator.consumer   > updating moz-owner file
  vcsreplicator.consumer   > new changesets 2d30fb72c11e
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into /repo/hg/mozilla/mozilla-central
  vcsreplicator.consumer processing hg-heads-1 from partition 2 offset 4
  vcsreplicator.consumer processing hg-repo-delete-1 from partition 2 offset 5
  vcsreplicator.consumer repository at /repo/hg/mozilla/mozilla-central deleted

Clean

  $ hgmo clean
