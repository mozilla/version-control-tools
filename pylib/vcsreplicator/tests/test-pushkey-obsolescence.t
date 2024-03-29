#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv
  $ standarduser

  $ hgmo create-repo obs scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /set-hgrc-option obs phases publish false
  $ hgmo exec hgssh /set-hgrc-option obs experimental evolution true
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs replicatehgrc
  recorded hgrc in replication log

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/obs) from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-hgrc-update-1: (repo: {moz}/obs) from partition 2 offset 1
  vcsreplicator.consumer writing hgrc: $TESTTMP/repos/obs/.hg/hgrc

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/obs client
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rebase =
  > [experimental]
  > evolution = true
  > [ui]
  > ssh = ssh -F $TESTTMP/ssh_config -i $TESTTMP/testuser -l user@example.com
  > EOF

  $ hgmo download-mirror-ssh-keys $TESTTMP
  SSH keys written to $TESTTMP
  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = ssh -F $TESTTMP/ssh_config -i $TESTTMP/mirror -l vcs-sync@mozilla.com
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg phase --public -f -r .
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/obs/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 3
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['77538e1ce4be']) from partition 2 offset 4
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 77538e1ce4be
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['77538e1ce4be'], last_push_id: 1) from partition 2 offset 5

Pruning a changeset locally and pushing should result in obsolescence marker on server

  $ touch file0
  $ hg -q commit -A -m 'add file0'
  $ touch file1
  $ hg -q commit -A -m 'add file1'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 2 changesets with 2 changes to 2 files
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/obs/rev/442ce5a124e001862e8bd6a8871d8b85e09bebd7
  remote:   https://hg.mozilla.org/obs/rev/11bec8a6b2a30ac170575ecfd7a06af5a75e2d77
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 6
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 7
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['11bec8a6b2a3']) from partition 2 offset 8
  vcsreplicator.consumer pulling 1 heads (11bec8a6b2a30ac170575ecfd7a06af5a75e2d77) and 2 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 2 changesets with 2 changes to 2 files
  vcsreplicator.consumer   > new changesets 442ce5a124e0:11bec8a6b2a3 (2 drafts)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['11bec8a6b2a3'], last_push_id: 2) from partition 2 offset 9

  $ hg -q up -r 1
  $ touch file2
  $ hg -q commit -A -m 'add file2'
  $ hg rebase -s 2 -d .
  rebasing 2:11bec8a6b2a3 "add file1"

  $ hg debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {*'user': 'Test User <someone@example.com>'} (glob)

  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 2 changesets with 1 changes to 2 files (+1 heads)
  remote: 1 new obsolescence markers
  remote: obsoleted 1 changesets
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/obs/rev/5dfb8fc50086c183d1cbd067e48c58307db16dac
  remote:   https://hg.mozilla.org/obs/rev/67b45555a21f4d9d470adc4f1ed3af63918f6414
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

Obsolescence marker should exist on master

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {*'user': 'Test User <someone@example.com>'} (glob)

Changegroup message written

  $ consumer --dump --partition 2
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    heads:
    - 67b45555a21f4d9d470adc4f1ed3af63918f6414
    name: hg-changegroup-2
    nodecount: 2
    path: '{moz}/obs'
    source: serve
  - _created: * (glob)
    key: dump0
    name: hg-pushkey-1
    namespace: obsolete
    new: 0096* (glob)
    old: ''
    path: '{moz}/obs'
    ret: 0
  - _created: * (glob)
    heads:
    - 67b45555a21f4d9d470adc4f1ed3af63918f6414
    last_push_id: 3
    name: hg-heads-1
    path: '{moz}/obs'

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 10
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 11
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['67b45555a21f']) from partition 2 offset 12
  vcsreplicator.consumer pulling 1 heads (67b45555a21f4d9d470adc4f1ed3af63918f6414) and 2 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r67b45555a21f4d9d470adc4f1ed3af63918f6414 -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 2 changesets with 1 changes to 1 files (+1 heads)
  vcsreplicator.consumer   > 1 new obsolescence markers
  vcsreplicator.consumer   > obsoleted 1 changesets
  vcsreplicator.consumer   > new changesets 5dfb8fc50086:67b45555a21f (2 drafts)
  vcsreplicator.consumer   > (run 'hg heads' to see heads)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1: (repo: {moz}/obs, namespace/key: obsolete/dump0) from partition 2 offset 13
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/obs for obsolete[dump0]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/obs obsolete dump0 '' '*' (glob)
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['67b45555a21f'], last_push_id: 3) from partition 2 offset 14

Obsolescence marker should have been replicated to hgweb

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {*'user': 'Test User <someone@example.com>'} (glob)

Creating obsolescence marker directly on server will result in replication

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete 67b45555a21f4d9d470adc4f1ed3af63918f6414
  no username found, using 'root@*' instead (glob)
  1 new obsolescence markers (hg52 !)
  obsoleted 1 changesets
  recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {*'user': 'Test User <someone@example.com>'} (glob)
  67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'root@*'} (glob)

  $ consumer --dump --partition 2
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    key: dump0
    name: hg-pushkey-1
    namespace: obsolete
    new: * (glob)
    old: ''
    path: '{moz}/obs'
    ret: 0

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 15
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 16
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1: (repo: {moz}/obs, namespace/key: obsolete/dump0) from partition 2 offset 17
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/obs for obsolete[dump0]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/obs obsolete dump0 '' '*' (glob)
  vcsreplicator.consumer   > 1 new obsolescence markers
  vcsreplicator.consumer   > obsoleted 1 changesets
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  11bec8a6b2a30ac170575ecfd7a06af5a75e2d77 67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {*'user': 'Test User <someone@example.com>'} (glob)
  67b45555a21f4d9d470adc4f1ed3af63918f6414 0 (*) {'user': 'root@*'} (glob)

Pushing obsolescence marker without bundle2 works

  $ touch file3
  $ hg -q commit -A -m file3
  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 2 files (+1 heads)
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/obs/rev/de9a6dc9203d34261c1e2bea219bdd6053d74dda
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ consumer --dump --partition 2
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    heads:
    - de9a6dc9203d34261c1e2bea219bdd6053d74dda
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/obs'
    source: serve
  - _created: * (glob)
    heads:
    - de9a6dc9203d34261c1e2bea219bdd6053d74dda
    last_push_id: 4
    name: hg-heads-1
    path: '{moz}/obs'

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 18
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 19
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['de9a6dc9203d']) from partition 2 offset 20
  vcsreplicator.consumer pulling 1 heads (de9a6dc9203d34261c1e2bea219bdd6053d74dda) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -rde9a6dc9203d34261c1e2bea219bdd6053d74dda -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files (+1 heads)
  vcsreplicator.consumer   > new changesets de9a6dc9203d (1 drafts)
  vcsreplicator.consumer   > (run 'hg heads' to see heads)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer mismatch between expected and actual changeset count: expected 1, got 2
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['de9a6dc9203d'], last_push_id: 4) from partition 2 offset 21

  $ hg rebase -s . -d 77538e1ce4be
  rebasing 5:de9a6dc9203d tip "file3" (hg59 !)
  rebasing 5:de9a6dc9203d "file3" (tip) (no-hg59 !)
  $ hg --config experimental.bundle2-exp=false push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 0 changes to 2 files (+1 heads)
  remote: 1 new obsolescence markers
  remote: obsoleted 1 changesets
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/obs/rev/33e52188e17750dee7ec7a6b05b5f707ebc2cba9
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ consumer --dump --partition 2
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    name: heartbeat-1
  - _created: * (glob)
    heads:
    - 33e52188e17750dee7ec7a6b05b5f707ebc2cba9
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/obs'
    source: serve
  - _created: * (glob)
    key: dump0
    name: hg-pushkey-1
    namespace: obsolete
    new: 0096* (glob)
    old: ''
    path: '{moz}/obs'
    ret: 0
  - _created: * (glob)
    heads:
    - 33e52188e17750dee7ec7a6b05b5f707ebc2cba9
    - 5dfb8fc50086c183d1cbd067e48c58307db16dac
    last_push_id: 5
    name: hg-heads-1
    path: '{moz}/obs'

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 22
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 23
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['33e52188e177']) from partition 2 offset 24
  vcsreplicator.consumer pulling 1 heads (33e52188e17750dee7ec7a6b05b5f707ebc2cba9) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r33e52188e17750dee7ec7a6b05b5f707ebc2cba9 -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 0 changes to 0 files (+1 heads)
  vcsreplicator.consumer   > 1 new obsolescence markers
  vcsreplicator.consumer   > obsoleted 1 changesets
  vcsreplicator.consumer   > new changesets 33e52188e177 (1 drafts)
  vcsreplicator.consumer   > (run 'hg heads' to see heads, 'hg merge' to merge)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1: (repo: {moz}/obs, namespace/key: obsolete/dump0) from partition 2 offset 25
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/obs for obsolete[dump0]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/obs obsolete dump0 '' '*' (glob)
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['33e52188e177', '5dfb8fc50086'], last_push_id: 5) from partition 2 offset 26
  $ consumer --onetime
  $ consumer --onetime

Now let's check what happens when replication is lagging

  $ touch file4
  $ hg -q commit -A -m file4
  $ hg -q push
  $ touch file5
  $ hg -q commit -A -m file5
  $ hg -q push
  $ touch file6
  $ hg -q commit -A -m file6
  $ hg -q push

  $ hg rebase -s 63d556ea5b9f -d 33e52188e177
  rebasing 8:63d556ea5b9f "file5"
  rebasing 9:87d2d20529e7 tip "file6" (hg59 !)
  rebasing 9:87d2d20529e7 "file6" (tip) (no-hg59 !)
  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 2 changesets with 0 changes to 3 files (+1 heads)
  remote: 2 new obsolescence markers
  remote: obsoleted 2 changesets
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/obs/rev/274cd1d986ab248aae0dfb9a902f7b6c823daec4
  remote:   https://hg.mozilla.org/obs/rev/27eddb78301f686b0894dadaa2deb6dfbb080123
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ hg rebase -s 274cd1d986ab -d 3694f932529e
  rebasing 10:274cd1d986ab "file5"
  rebasing 11:27eddb78301f tip "file6" (hg59 !)
  rebasing 11:27eddb78301f "file6" (tip) (no-hg59 !)
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 2 changesets with 0 changes to 3 files (+1 heads)
  remote: 2 new obsolescence markers
  remote: obsoleted 2 changesets
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/obs/rev/4dabe70969cafe3378dd579fb186ce31d168ff0a
  remote:   https://hg.mozilla.org/obs/rev/84b66e579087f83fdd8ea21456fe68a1c9b60cbe
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ hg log -G
  @  changeset:   13:84b66e579087
  |  tag:         tip
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     file6
  |
  o  changeset:   12:4dabe70969ca
  |  parent:      7:3694f932529e
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     file5
  |
  o  changeset:   7:3694f932529e
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     file4
  |
  o  changeset:   6:33e52188e177
  |  parent:      0:77538e1ce4be
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     file3
  |
  | o  changeset:   4:67b45555a21f
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     add file1
  | |
  | o  changeset:   3:5dfb8fc50086
  | |  parent:      1:442ce5a124e0
  | |  user:        Test User <someone@example.com>
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     add file2
  | |
  | o  changeset:   1:442ce5a124e0
  |/   user:        Test User <someone@example.com>
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     add file0
  |
  o  changeset:   0:77538e1ce4be
     user:        Test User <someone@example.com>
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 27
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 28
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['3694f932529e']) from partition 2 offset 29
  vcsreplicator.consumer pulling 1 heads (3694f932529eff9a4b78fafab6097f27f3c37daa) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r3694f932529eff9a4b78fafab6097f27f3c37daa -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 3694f932529e (1 drafts)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['3694f932529e', '5dfb8fc50086'], last_push_id: 6) from partition 2 offset 30
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 31
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 32
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['63d556ea5b9f']) from partition 2 offset 33
  vcsreplicator.consumer pulling 1 heads (63d556ea5b9faf08c8c41864c1fcaf3d57f986c8) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r63d556ea5b9faf08c8c41864c1fcaf3d57f986c8 -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 63d556ea5b9f (1 drafts)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['63d556ea5b9f', '5dfb8fc50086'], last_push_id: 7) from partition 2 offset 34
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 35
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 36
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['87d2d20529e7']) from partition 2 offset 37
  vcsreplicator.consumer pulling 1 heads (87d2d20529e71d92b847f1bad94c8ebb00203230) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r87d2d20529e71d92b847f1bad94c8ebb00203230 -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 87d2d20529e7 (1 drafts)
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['87d2d20529e7', '5dfb8fc50086'], last_push_id: 8) from partition 2 offset 38

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 39
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 40
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['27eddb78301f']) from partition 2 offset 41
  vcsreplicator.consumer pulling 1 heads (27eddb78301f686b0894dadaa2deb6dfbb080123) and 2 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r27eddb78301f686b0894dadaa2deb6dfbb080123 -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 2 changesets with 0 changes to 0 files (+1 heads)
  vcsreplicator.consumer   > 2 new obsolescence markers
  vcsreplicator.consumer   > obsoleted 2 changesets
  vcsreplicator.consumer   > new changesets 274cd1d986ab:27eddb78301f (2 drafts)
  vcsreplicator.consumer   > (run 'hg heads .' to see heads, 'hg merge' to merge)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1: (repo: {moz}/obs, namespace/key: obsolete/dump0) from partition 2 offset 42
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/obs for obsolete[dump0]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/obs obsolete dump0 '' '*' (glob)
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['27eddb78301f', '3694f932529e', '5dfb8fc50086'], last_push_id: 9) from partition 2 offset 43
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 44
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 45
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/obs, heads: ['84b66e579087']) from partition 2 offset 46
  vcsreplicator.consumer pulling 1 heads (84b66e579087f83fdd8ea21456fe68a1c9b60cbe) and 2 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/obs into $TESTTMP/repos/obs
  vcsreplicator.consumer   $ hg pull -r84b66e579087f83fdd8ea21456fe68a1c9b60cbe -- ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 2 changesets with 0 changes to 2 files (+1 heads)
  vcsreplicator.consumer   > 2 new obsolescence markers
  vcsreplicator.consumer   > obsoleted 2 changesets
  vcsreplicator.consumer   > new changesets 4dabe70969ca:84b66e579087 (2 drafts)
  vcsreplicator.consumer   > (run 'hg heads' to see heads, 'hg merge' to merge)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 2 changesets into $TESTTMP/repos/obs
  $ consumer --onetime
  vcsreplicator.consumer processing hg-pushkey-1: (repo: {moz}/obs, namespace/key: obsolete/dump0) from partition 2 offset 47
  vcsreplicator.consumer executing pushkey on $TESTTMP/repos/obs for obsolete[dump0]
  vcsreplicator.consumer   $ hg debugpushkey $TESTTMP/repos/obs obsolete dump0 '' '*' (glob)
  vcsreplicator.consumer   > True
  vcsreplicator.consumer   [0]
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/obs, heads: ['84b66e579087', '5dfb8fc50086'], last_push_id: 10) from partition 2 offset 48

  $ consumer --dump --partition 2
  []

Local mirror and server should have same state

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs log -G > log.remote
  $ hg -R $TESTTMP/repos/obs log -G > log.local
  $ diff -U0 log.local log.remote

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete > obs.remote
  $ hg -R $TESTTMP/repos/obs debugobsolete > obs.local
  $ diff -U0 obs.local obs.remote

Cleanup

  $ hgmo clean
