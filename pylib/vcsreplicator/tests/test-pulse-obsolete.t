#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ pulse create-queue exchange/hgpushes/v1 v1
  $ pulse create-queue exchange/hgpushes/v2 v2

  $ standarduser

Obsolescence markers are turned into pulse events

  $ hgmo create-repo obs scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /set-hgrc-option obs phases publish false
  $ hgmo exec hgssh /set-hgrc-option obs experimental evolution all
  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs replicatehgrc
  recorded hgrc in replication log

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/obs obs
  $ cd obs
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rebase =
  > [experimental]
  > evolution = all
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg phase --public -f -r .
  $ hg -q push
  $ touch file0
  $ hg -q commit -A -m file0
  $ touch file1
  $ hg -q commit -A -m file1
  $ hg -q push

There is a race between multiple repo events and the pulse consumer processing
them. So disable the pulse consumer until all repo changes have been made.

  $ hgmo exec hgssh supervisorctl stop pulsenotifier
  pulsenotifier: stopped

  $ hg rebase -s . -d 0
  rebasing 2:4da703b7f59b "file1" (tip)
  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: 1 new obsolescence markers
  remote: obsoleted 1 changesets
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/obs/rev/7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ hg debugobsolete
  4da703b7f59b720f524f709aa07eed3182ba1acd 7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2 0 (*) {'user': 'Test User <someone@example.com>'} (glob)

  $ paconsumer --wait-for-n 13
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a hg-hgrc-update-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-pushkey-1 message

Create an obsolescence marker on the server

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete 7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2
  no username found, using 'root@*' instead (glob)
  obsoleted 1 changesets
  recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ hgmo exec hgssh /var/hg/venv_pash/bin/hg -R /repo/hg/mozilla/obs debugobsolete
  4da703b7f59b720f524f709aa07eed3182ba1acd 7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2 0 (*) {'user': 'Test User <someone@example.com>'} (glob)
  7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2 0 (*) {'user': 'root@*'} (glob)

Send a precursor marker referencing a node unknown to the server

  $ hg -q up -r 0
  $ touch precursor
  $ hg -q commit -A -m 'obsolete never sent'
  $ hg commit --amend -m 'first amend'
  $ hg commit --amend -m 'second amend'
  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 2 files (+1 heads)
  remote: recorded push in pushlog
  remote: 2 new obsolescence markers
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/obs/rev/7066e27cce8ca811f9f80da78e330c72af5a49f8
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

Commit message with multiple lines works

  $ hg -q up -r 0
  $ cat > multiline << EOF
  > first line
  > second line
  > third line
  > EOF
  $ hg -q commit -A -l multiline
  $ cat >> multiline << EOF
  > fourth line
  > fifth line
  > EOF
  $ hg commit --amend -l multiline
  $ hg push -f
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/obs
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 2 files (+1 heads)
  remote: recorded push in pushlog
  remote: 2 new obsolescence markers
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/obs/rev/821cb8db71235562a3ee752f0b67502e93835a9f
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  remote: recorded updates to obsolete in replication log in \d+\.\d+s (re)

  $ paconsumer --wait-for-n 24
  got a heartbeat-1 message
  got a hg-repo-init-2 message
  got a hg-hgrc-update-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-pushkey-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-pushkey-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-pushkey-1 message
  got a heartbeat-1 message
  got a heartbeat-1 message
  got a hg-changegroup-2 message
  got a hg-pushkey-1 message

  $ hgmo exec hgssh supervisorctl start pulsenotifier
  pulsenotifier: started

  $ pulseconsumer --wait-for-no-lag

  $ pulse dump-messages exchange/hgpushes/v2 v2
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      repo_url: https://hg.mozilla.org/obs
    type: newrepo.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      heads:
      - 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=0&endID=1
        push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=0&endID=1
        pushid: 1
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/obs
      source: serve
    type: changegroup.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      heads:
      - 4da703b7f59b720f524f709aa07eed3182ba1acd
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=1&endID=2
        push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=1&endID=2
        pushid: 2
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/obs
      source: serve
    type: changegroup.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      heads:
      - 7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=2&endID=3
        push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=2&endID=3
        pushid: 3
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/obs
      source: serve
    type: changegroup.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      markers:
      - precursor:
          desc: file1
          known: true
          node: 4da703b7f59b720f524f709aa07eed3182ba1acd
          push:
            push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=1&endID=2
            push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=1&endID=2
            pushid: 2
            time: \d+ (re)
            user: user@example.com
          visible: false
        successors:
        - desc: file1
          known: true
          node: 7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2
          push:
            push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=2&endID=3
            push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=2&endID=3
            pushid: 3
            time: \d+ (re)
            user: user@example.com
          visible: false
        time: \d+\.\d+ (re)
        user: Test User <someone@example.com>
      repo_url: https://hg.mozilla.org/obs
    type: obsolete.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      markers:
      - precursor:
          desc: file1
          known: true
          node: 7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2
          push:
            push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=2&endID=3
            push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=2&endID=3
            pushid: 3
            time: \d+ (re)
            user: user@example.com
          visible: false
        successors: []
        time: \d+\.\d+ (re)
        user: root@* (glob)
      repo_url: https://hg.mozilla.org/obs
    type: obsolete.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      heads:
      - 7066e27cce8ca811f9f80da78e330c72af5a49f8
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=3&endID=4
        push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=3&endID=4
        pushid: 4
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/obs
      source: serve
    type: changegroup.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      markers:
      - precursor:
          desc: null
          known: false
          node: 506deb6d051199c92e6681021bd819fe7bf57ed0
          push: null
          visible: null
        successors:
        - desc: second amend
          known: true
          node: 7066e27cce8ca811f9f80da78e330c72af5a49f8
          push:
            push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=3&endID=4
            push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=3&endID=4
            pushid: 4
            time: \d+ (re)
            user: user@example.com
          visible: true
        time: \d+\.\d+ (re)
        user: Test User <someone@example.com>
      - precursor:
          desc: null
          known: false
          node: 8e81a192ded91c8c10b727345689c8ab80448750
          push: null
          visible: null
        successors:
        - desc: null
          known: false
          node: 506deb6d051199c92e6681021bd819fe7bf57ed0
          push: null
          visible: null
        time: \d+\.\d+ (re)
        user: Test User <someone@example.com>
      repo_url: https://hg.mozilla.org/obs
    type: obsolete.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      heads:
      - 821cb8db71235562a3ee752f0b67502e93835a9f
      pushlog_pushes:
      - push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=4&endID=5
        push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=4&endID=5
        pushid: 5
        time: \d+ (re)
        user: user@example.com
      repo_url: https://hg.mozilla.org/obs
      source: serve
    type: changegroup.1
  - _meta:
      exchange: exchange/hgpushes/v2
      routing_key: obs
    data:
      markers:
      - precursor:
          desc: null
          known: false
          node: 0a1055f8c9cb8d183d9e5b843e182038f51cbe6e
          push: null
          visible: null
        successors: []
        time: \d+\.\d+ (re)
        user: Test User <someone@example.com>
      - precursor:
          desc: null
          known: false
          node: 2d43215925d94eb9e5792ae70344b3c8be755e5f
          push: null
          visible: null
        successors:
        - desc: 'first line
  
            second line
  
            third line
  
            fourth line
  
            fifth line'
          known: true
          node: 821cb8db71235562a3ee752f0b67502e93835a9f
          push:
            push_full_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&full=1&startID=4&endID=5
            push_json_url: https://hg.mozilla.org/obs/json-pushes?version=2&startID=4&endID=5
            pushid: 5
            time: \d+ (re)
            user: user@example.com
          visible: true
        time: \d+\.\d+ (re)
        user: Test User <someone@example.com>
      repo_url: https://hg.mozilla.org/obs
    type: obsolete.1

  $ cd ..

Cleanup

  $ hgmo clean
