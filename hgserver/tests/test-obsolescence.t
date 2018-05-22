#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo users/user_example.com/repo-1 scm_level_1
  (recorded repository creation in replication log)

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1

Mark repo as non-publishing
  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 3
  > EOF
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? Repository marked as non-publishing: draft changesets will remain in the draft phase when pushed.

Enable obsolescence on the repo

  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 5
  > EOF
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? Obsolescence is now enabled for this repository.
  
  Obsolescence is currently an experimental feature. It may be disabled at any
  time. Your obsolescence data may be lost at any time. You have been warned.
  
  Enjoy living on the edge.

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 cat /repo/hg/mozilla/users/user_example.com/repo-1/.hg/hgrc
  [phases]
  publish = False
  
  [experimental]
  evolution = all
  

Create initial repo content

  $ cd repo-1
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rebase=
  > 
  > [experimental]
  > evolution=all
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial
  $ touch bar
  $ hg -q commit -A -m bar
  $ hg -q up -r 0
  $ touch baz
  $ hg -q commit -A -m baz

  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/users/user_example.com/repo-1
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 3 files (+1 heads)
  remote: recorded push in pushlog
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/ba1c6c2be69c46fed329d3795c9d906d252fdaf7
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/a9e729deb87c57f067a862aff25644d62d6bac16
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

Verify pushlog state on hgweb machine

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_tools/bin/hg --hidden -R /repo/hg/mozilla/users/user_example.com/repo-1 log -r 0:tip -T '{rev}:{node|short} {phase} {pushid} {pushuser}\n'
  0:77538e1ce4be draft 1 user@example.com
  1:ba1c6c2be69c draft 1 user@example.com
  2:a9e729deb87c draft 1 user@example.com

  $ cd ..

Create another clone

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1 repo-1-clone
  $ cat >> repo-1-clone/.hg/hgrc << EOF
  > [experimental]
  > evolution=all
  > EOF

Create some obsolescence markers

  $ cd repo-1
  $ hg rebase -s 1 -d 2
  rebasing 1:ba1c6c2be69c "bar"
  $ hg debugobsolete
  ba1c6c2be69c46fed329d3795c9d906d252fdaf7 5217e2ac5b1538d1630aa54377056dbfab270508 0 (* +0000) {'user': 'Test User <someone@example.com>'} (glob)

  $ hg push ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/users/user_example.com/repo-1
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files
  remote: recorded push in pushlog
  remote: 1 new obsolescence markers
  remote: obsoleted 1 changesets
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/5217e2ac5b1538d1630aa54377056dbfab270508
  remote: recorded changegroup in replication log in \d\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)
  $ cd ..

Pulling should get the obsmarkers

  $ cd repo-1-clone
  $ hg pull
  pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/users/user_example.com/repo-1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 1 files
  1 new obsolescence markers
  obsoleted 1 changesets
  (run 'hg update' to get a working copy)
  $ hg debugobsolete
  ba1c6c2be69c46fed329d3795c9d906d252fdaf7 5217e2ac5b1538d1630aa54377056dbfab270508 0 (* +0000) {'user': 'Test User <someone@example.com>'} (glob)

  $ cd ..

Obsolescence markers should have gotten pulled on hgweb mirror

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/users/user_example.com/repo-1 debugobsolete
  ba1c6c2be69c46fed329d3795c9d906d252fdaf7 5217e2ac5b1538d1630aa54377056dbfab270508 0 (* +0000) {'user': 'Test User <someone@example.com>'} (glob)

The pushlog should have new push

  $ hgmo exec hgweb0 /var/hg/venv_tools/bin/hg --hidden -R /repo/hg/mozilla/users/user_example.com/repo-1 log -r 0:tip -T '{rev}:{node|short} {phase} {pushid} {pushuser}\n'
  0:77538e1ce4be draft 1 user@example.com
  1:ba1c6c2be69c draft 1 user@example.com
  2:a9e729deb87c draft 1 user@example.com
  3:5217e2ac5b15 draft 2 user@example.com

Pushing a changeset then hiding it works

  $ cd repo-1
  $ hg -q up -r 5217e2ac5b15
  $ touch file0
  $ hg -q commit -A -m head1
  $ hg -q up -r 5217e2ac5b15
  $ touch file1
  $ hg -q commit -A -m head2

  $ hg push -r 8713015ee6f2 ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/users/user_example.com/repo-1
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/8713015ee6f2dc22a64a7821684d7119323dc119
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  $ hg push -f -r 6ddbc9389e71 ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/users/user_example.com/repo-1
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/6ddbc9389e710d9b4f3c880d7c99320f9581dbd5
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ hg rebase -s 6ddbc9389e71 -d 8713015ee6f2
  rebasing 5:6ddbc9389e71 "head2" (tip)
  $ hg push -f ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/users/user_example.com/repo-1
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files
  remote: recorded push in pushlog
  remote: 1 new obsolescence markers
  remote: obsoleted 1 changesets
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/042a67bdbae8a8b4c4b071303ad92484cf1746b0
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ hg debugobsolete
  ba1c6c2be69c46fed329d3795c9d906d252fdaf7 5217e2ac5b1538d1630aa54377056dbfab270508 0 (*) {'user': 'Test User <someone@example.com>'} (glob)
  6ddbc9389e710d9b4f3c880d7c99320f9581dbd5 042a67bdbae8a8b4c4b071303ad92484cf1746b0 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/users/user_example.com/repo-1 debugobsolete
  ba1c6c2be69c46fed329d3795c9d906d252fdaf7 5217e2ac5b1538d1630aa54377056dbfab270508 0 (*) {'user': 'Test User <someone@example.com>'} (glob)
  6ddbc9389e710d9b4f3c880d7c99320f9581dbd5 042a67bdbae8a8b4c4b071303ad92484cf1746b0 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

  $ hgmo exec hgweb0 /var/hg/venv_tools/bin/hg --hidden -R /repo/hg/mozilla/users/user_example.com/repo-1 log -r 0:tip -T '{rev}:{node|short} {phase} {pushid} {pushuser}\n'
  0:77538e1ce4be draft 1 user@example.com
  1:ba1c6c2be69c draft 1 user@example.com
  2:a9e729deb87c draft 1 user@example.com
  3:5217e2ac5b15 draft 2 user@example.com
  4:8713015ee6f2 draft 3 user@example.com
  5:6ddbc9389e71 draft 4 user@example.com
  6:042a67bdbae8 draft 5 user@example.com

Blowing away the repo on hgweb and re-cloning should retain pushlog and hidden changesets

  $ hgmo exec hgweb0 rm -rf /repo/hg/mozilla/users/user_example.com/repo-1
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg init /repo/hg/mozilla/users/user_example.com/repo-1
  $ hgmo exec hgweb0 /var/hg/version-control-tools/scripts/repo-permissions /repo/hg/mozilla/users/user_example.com/repo-1 hg hg wwr
  /repo/hg/mozilla/users/user_example.com/repo-1: changed owner on 5; mode on 5
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg --hidden -R /repo/hg/mozilla/users/user_example.com/repo-1 replicatesync
  wrote synchronization message into replication log
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ hgmo exec hgweb0 /var/hg/venv_tools/bin/hg --hidden -R /repo/hg/mozilla/users/user_example.com/repo-1 log -r 0:tip -T '{rev}:{node|short} {phase} {pushid} {pushuser}\n'
  0:77538e1ce4be draft 1 user@example.com
  1:ba1c6c2be69c draft 1 user@example.com
  2:a9e729deb87c draft 1 user@example.com
  3:5217e2ac5b15 draft 2 user@example.com
  4:8713015ee6f2 draft 3 user@example.com
  5:6ddbc9389e71 draft 4 user@example.com
  6:042a67bdbae8 draft 5 user@example.com

  $ cd ..

Create a repo that only has the createmarkers feature enabled

  $ hgmo create-repo integration/autoland scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /set-hgrc-option integration/autoland experimental evolution createmarkers
  $ hgmo exec hgssh /set-hgrc-option integration/autoland phases publish false
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/integration/autoland replicatehgrc
  recorded hgrc in replication log

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/integration/autoland autoland
  $ cd autoland
  $ cat >> .hg/hgrc << EOF
  > [experimental]
  > evolution = all
  > [extensions]
  > rebase =
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push
  $ touch file0
  $ hg -q commit -A -m file0
  $ hg -q push
  $ hg -q up -r 0
  $ touch file1
  $ hg -q commit -A -m file1
  $ hg -q push -f
  $ hg rebase -s . -d 1
  rebasing 2:5fb779ae39de "file1" (tip)

Pushing should not send obsolescence markers because marker exchange isn't allowed
and we're not in the allowed user list

  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/integration/autoland
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/integration/autoland/rev/d57129f00b2f329fc2cf3371a0c28796bcfbde1c
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/integration/autoland debugobsolete

hgweb advertise marker exchange

  $ http --no-headers "${HGWEB_0_URL}integration/autoland?cmd=capabilities"
  200
  
  lookup changegroupsubset branchmap pushkey known getbundle unbundlehash batch streamreqs=generaldelta,revlogv1 bundle2=HG20%0Achangegroup%3D01%2C02%0Adigests%3Dmd5%2Csha1%2Csha512%0Aerror%3Dabort%2Cunsupportedcontent%2Cpushraced%2Cpushkey%0Ahgtagsfnodes%0Alistkeys%0Aobsmarkers%3DV0%2CV1%0Aphases%3Dheads%0Apushkey%0Aremote-changegroup%3Dhttp%2Chttps unbundle=HG10GZ,HG10BZ,HG10UN httpheader=6144 httppostargs httpmediatype=0.1rx,0.1tx,0.2tx compression=zstd,zlib pushlog

Allow this user to send obsolescence markers (since the per-repo hgrc will get replicated
and take precedence on the mirror, we need to add the allowed user from the replication
processes on both server and mirror)

  $ hgmo exec hgssh /set-hgrc-option integration/autoland obshacks obsolescenceexchangeusers "user@example.com,vcs-sync@mozilla.com,hg"
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/integration/autoland replicatehgrc
  recorded hgrc in replication log

Pushing again should send obsolescence markers

  $ hg rebase -s . -d 0
  rebasing 3:d57129f00b2f "file1" (tip)
  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/integration/autoland
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: 2 new obsolescence markers
  remote: obsoleted 2 changesets
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/integration/autoland/rev/9e2d548e5f1f94b9172cfeb77b53f5943722b594
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/integration/autoland debugobsolete
  5fb779ae39de4af3229a53c35d46117e98fb5f83 d57129f00b2f329fc2cf3371a0c28796bcfbde1c 0 (*) {'user': 'Test User <someone@example.com>'} (glob)
  d57129f00b2f329fc2cf3371a0c28796bcfbde1c 9e2d548e5f1f94b9172cfeb77b53f5943722b594 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

And they should get replicated to mirrors

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/integration/autoland debugobsolete
  5fb779ae39de4af3229a53c35d46117e98fb5f83 d57129f00b2f329fc2cf3371a0c28796bcfbde1c 0 (*) {'user': 'Test User <someone@example.com>'} (glob)
  d57129f00b2f329fc2cf3371a0c28796bcfbde1c 9e2d548e5f1f94b9172cfeb77b53f5943722b594 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

hgweb should still advertise marker exchange

  $ http --no-headers "${HGWEB_0_URL}integration/autoland?cmd=capabilities"
  200
  
  lookup changegroupsubset branchmap pushkey known getbundle unbundlehash batch streamreqs=generaldelta,revlogv1 bundle2=HG20%0Achangegroup%3D01%2C02%0Adigests%3Dmd5%2Csha1%2Csha512%0Aerror%3Dabort%2Cunsupportedcontent%2Cpushraced%2Cpushkey%0Ahgtagsfnodes%0Alistkeys%0Aobsmarkers%3DV0%2CV1%0Aphases%3Dheads%0Apushkey%0Aremote-changegroup%3Dhttp%2Chttps unbundle=HG10GZ,HG10BZ,HG10UN httpheader=6144 httppostargs httpmediatype=0.1rx,0.1tx,0.2tx compression=zstd,zlib pushlog

  $ cd ..

  $ hgmo clean
