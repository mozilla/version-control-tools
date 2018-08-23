#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ standarduser

Create a repo as the origin repo and make copies

  $ hgmo exec hgssh /create-repo mozilla-unified scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /create-repo repo1 scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /create-repo repo2 scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /create-repo repo3 scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /create-repo stage scm_level_1
  (recorded repository creation in replication log)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-unified
  $ cd mozilla-unified
  $ echo bar > foo
  $ hg -q addremove
  $ hg -q commit -A -m "SOURCE"
  $ hg -q push ssh://${SSH_SERVER}:${SSH_PORT}/repo1
  $ hg -q push ssh://${SSH_SERVER}:${SSH_PORT}/repo2
  $ hg -q push ssh://${SSH_SERVER}:${SSH_PORT}/repo3
  $ hg -q push ssh://${SSH_SERVER}:${SSH_PORT}/stage

  $ hgmo exec hgssh sudo /var/hg/venv_tools/bin/python /var/hg/version-control-tools/scripts/repo-permissions /repo/hg/mozilla/stage hg-aggregate hg-aggregate wwr
  /repo/hg/mozilla/stage: changed owner on *; mode on * (glob)
  $ hgmo exec hgssh sudo /var/hg/venv_tools/bin/python /var/hg/version-control-tools/scripts/repo-permissions /repo/hg/mozilla/mozilla-unified hg-aggregate hg-aggregate wwr
  /repo/hg/mozilla/mozilla-unified: changed owner on *; mode on * (glob)

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo1 replicatesync
  wrote synchronization message into replication log
  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo2 replicatesync
  wrote synchronization message into replication log
  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo3 replicatesync
  wrote synchronization message into replication log

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

Fill the origin repos with some commits

  $ cd ..
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/repo1
  $ cd repo1
  $ echo barz > barz
  $ hg -q addremove
  $ hg -q commit -A -m "repo1 commit0"
  $ hg -q push
  $ echo barbarz > barz
  $ hg -q commit -A -m "repo1 commit1"
  $ hg -q push
  $ echo barbarbarz > barz
  $ hg -q commit -A -m "repo1 commit2"
  $ hg -q push

  $ cd ..
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/repo2
  $ cd repo2
  $ echo barz > barz
  $ hg -q addremove
  $ hg -q commit -A -m "repo2 commit0"
  $ hg -q push
  $ echo barbarz > barz
  $ hg -q commit -A -m "repo2 commit1"
  $ hg -q push
  $ echo barbarbarz > barz
  $ hg -q commit -A -m "repo2 commit2"
  $ hg -q push

  $ cd ..
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/repo3
  $ cd repo3
  $ echo barz > barz
  $ hg -q addremove
  $ hg -q commit -A -m "repo3 commit0"
  $ hg -q push
  $ echo barbarz > barz
  $ hg -q commit -A -m "repo3 commit1"
  $ hg -q push
  $ echo barbarbarz > barz
  $ hg -q commit -A -m "repo3 commit2"
  $ hg -q push

Activate the unification daemon

  $ hgmo exec hgssh sudo -u hg-aggregate -g hg-aggregate /var/hg/venv_tools/bin/python -u /var/hg/version-control-tools/hgext/unifyrepo/unify-daemon.py /var/hg/venv_tools/bin/hg /etc/mercurial/unify-mozilla-unified.ini --maximum 1
  pulling /repo/hg/mozilla/repo1 into /repo/hg/mozilla/stage
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  new changesets d9233cc30325:010a55e3c12e
  recorded changegroup in replication log in * (glob)
  pulling /repo/hg/mozilla/repo2 into /repo/hg/mozilla/stage
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 0 changes to 1 files (+1 heads)
  new changesets 2c933d19cfc5:5d9296a9425e
  recorded changegroup in replication log in * (glob)
  pulling /repo/hg/mozilla/repo3 into /repo/hg/mozilla/stage
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 0 changes to 1 files (+1 heads)
  new changesets d781fe32e4e7:a8614ce316d1
  recorded changegroup in replication log in * (glob)
  obtained pushlog info for 4/4 revisions from 4 pushes from repo1
  obtained pushlog info for 4/4 revisions from 4 pushes from repo2
  obtained pushlog info for 4/4 revisions from 4 pushes from repo3
  aggregating 4/4 revisions for 1 heads from repo1
  aggregating 4/4 revisions for 1 heads from repo2
  aggregating 4/4 revisions for 1 heads from repo3
  aggregating 10/10 nodes from 12 original pushes
  10/10 nodes will be pulled
  consolidated into 3 pulls from 10 unique pushes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 4 changes to 2 files
  new changesets 1850d0344b46:010a55e3c12e
  recorded changegroup in replication log in * (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 0 changes to 0 files (+1 heads)
  new changesets 2c933d19cfc5:5d9296a9425e
  recorded changegroup in replication log in * (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 0 changes to 0 files (+1 heads)
  new changesets d781fe32e4e7:a8614ce316d1
  recorded changegroup in replication log in * (glob)
  inserting 10 pushlog entries
  writing 3 bookmarks
  wrote synchronization message into replication log

Confirm unified repo replicates to all mirrors

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-unified log -G
  o  changeset:   9:a8614ce316d1
  |  bookmark:    repo3
  |  tag:         tip
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     repo3 commit2
  |
  o  changeset:   8:9c550f047f2b
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     repo3 commit1
  |
  o  changeset:   7:d781fe32e4e7
  |  parent:      0:1850d0344b46
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     repo3 commit0
  |
  | o  changeset:   6:5d9296a9425e
  | |  bookmark:    repo2
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo2 commit2
  | |
  | o  changeset:   5:6027057bb2b0
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo2 commit1
  | |
  | o  changeset:   4:2c933d19cfc5
  |/   parent:      0:1850d0344b46
  |    user:        Test User <someone@example.com>
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     repo2 commit0
  |
  | o  changeset:   3:010a55e3c12e
  | |  bookmark:    repo1
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo1 commit2
  | |
  | o  changeset:   2:27d484479ab4
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo1 commit1
  | |
  | o  changeset:   1:d9233cc30325
  |/   user:        Test User <someone@example.com>
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     repo1 commit0
  |
  o  changeset:   0:1850d0344b46
     user:        Test User <someone@example.com>
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     SOURCE
  

  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/mozilla-unified log -G
  o  changeset:   9:a8614ce316d1
  |  bookmark:    repo3
  |  tag:         tip
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     repo3 commit2
  |
  o  changeset:   8:9c550f047f2b
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     repo3 commit1
  |
  o  changeset:   7:d781fe32e4e7
  |  parent:      0:1850d0344b46
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     repo3 commit0
  |
  | o  changeset:   6:5d9296a9425e
  | |  bookmark:    repo2
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo2 commit2
  | |
  | o  changeset:   5:6027057bb2b0
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo2 commit1
  | |
  | o  changeset:   4:2c933d19cfc5
  |/   parent:      0:1850d0344b46
  |    user:        Test User <someone@example.com>
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     repo2 commit0
  |
  | o  changeset:   3:010a55e3c12e
  | |  bookmark:    repo1
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo1 commit2
  | |
  | o  changeset:   2:27d484479ab4
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     repo1 commit1
  | |
  | o  changeset:   1:d9233cc30325
  |/   user:        Test User <someone@example.com>
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     repo1 commit0
  |
  o  changeset:   0:1850d0344b46
     user:        Test User <someone@example.com>
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     SOURCE
  

Clean

  $ hgmo clean
