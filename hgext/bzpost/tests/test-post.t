#require docker
  $ $TESTDIR/testing/docker-control.py start-bmo bzpost-test-post $HGPORT1
  waiting for Bugzilla to start
  Bugzilla accessible on http://*:$HGPORT1/ (glob)

  $ export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT1

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bzpost = $TESTDIR/hgext/bzpost
  > localmozrepo = $TESTDIR/testing/local-mozilla-repos.py
  > strip =
  > 
  > [localmozrepo]
  > readuri = http://localhost:$HGPORT/
  > writeuri = http://localhost:$HGPORT/
  > 
  > [bugzilla]
  > username = admin@example.com
  > password = password
  > url = ${BUGZILLA_URL}/rest
  > 
  > [bzpost]
  > debugcomments = True
  > EOF

  $ hg init mozilla-central
  $ cd mozilla-central
  $ cat >> .hg/hgrc << EOF
  > [web]
  > push_ssl = False
  > allow_push = *
  > EOF

  $ echo initial > foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg phase --public -r .
  $ cd ..

  $ mkdir integration
  $ hg clone mozilla-central integration/mozilla-inbound > /dev/null
  $ cp mozilla-central/.hg/hgrc integration/mozilla-inbound/.hg/hgrc

  $ hg clone mozilla-central try > /dev/null
  $ cp mozilla-central/.hg/hgrc try/.hg/hgrc
  $ cd try
  $ cat >> .hg/hgrc << EOF
  > [phases]
  > publish = False
  > EOF
  $ cd ..

  $ cat >> hgweb << EOF
  > [paths]
  > / = *
  > EOF
  $ hg serve -d -p $HGPORT --pid-file hg.pid --web-conf hgweb
  $ cat hg.pid >> $DAEMON_PIDS

  $ $TESTDIR/testing/bugzilla.py create-bug TestProduct TestComponent bug1

Pushing to mozilla-inbound will result in bug being updated

  $ hg clone mozilla-central mi-push > /dev/null
  $ cd mi-push
  $ echo mc > foo
  $ hg commit -m 'Bug 1 - Commit to inbound'
  $ hg push http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  recording push in bug 1

  $ $TESTDIR/testing/bugzilla.py dump-bug 1
  Bug 1:
    comments:
    - id: 1
      text: ''
    - id: 2
      text: http://localhost:$HGPORT/integration/mozilla-inbound/rev/b507e8e33160
    summary: bug1

Pushing multiple changesets with multiple bugs will result in bug being updated

  $ $TESTDIR/testing/bugzilla.py create-bug TestProduct TestComponent bug2
  $ $TESTDIR/testing/bugzilla.py create-bug TestProduct TestComponent bug3

  $ echo 2_1 > foo
  $ hg commit -m 'Bug 2 - First commit'
  $ echo 2_2 > foo
  $ hg commit -m 'Bug 2 - Second commit'
  $ echo 3_1 > foo
  $ hg commit -m 'Bug 3 - Another bug'
  $ hg push http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  recording push in bug 2
  recording push in bug 3

  $ $TESTDIR/testing/bugzilla.py dump-bug 2 3
  Bug 2:
    comments:
    - id: 3
      text: ''
    - id: 5
      text: 'http://localhost:$HGPORT/integration/mozilla-inbound/rev/a224eb610808
  
        http://localhost:$HGPORT/integration/mozilla-inbound/rev/e3b5f3c3c45d'
    summary: bug2
  Bug 3:
    comments:
    - id: 4
      text: ''
    - id: 6
      text: http://localhost:$HGPORT/integration/mozilla-inbound/rev/abe0245372d4
    summary: bug3

  $ cd ..

Pushing to Try will post TBPL comment

  $ $TESTDIR/testing/bugzilla.py create-bug TestProduct TestComponent bug4

  $ hg clone -r 0 try client > /dev/null
  $ cd client
  $ echo expected > foo
  $ hg commit -m 'Bug 4 - Add foo'
  $ echo foo > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  recording TBPL push in bug 4

  $ $TESTDIR/testing/bugzilla.py dump-bug 4
  Bug 4:
    comments:
    - id: 7
      text: ''
    - id: 8
      text: https://tbpl.mozilla.org/?tree=Try&rev=311111800824
    summary: bug4

  $ cd ..

Public changesets pushed to Try will be ignored if no bug in draft changesets

  $ $TESTDIR/testing/bugzilla.py create-bug TestProduct TestComponent bug5
  $ hg clone -r 0 try no-bug-in-draft > /dev/null
  $ cd no-bug-in-draft
  $ echo no-bug-in-draft > foo
  $ hg commit -m 'Bug 5 - This should be irrelevant'
  $ hg phase --public -r .
  $ echo foo > foo
  $ hg commit -m 'New draft changeset without bug'
  $ echo try > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push --force http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files (+1 heads)

  $ $TESTDIR/testing/bugzilla.py dump-bug 5
  Bug 5:
    comments:
    - id: 9
      text: ''
    summary: bug5

  $ cd ..

Public changesets pushed to Try will be ignored if a bug in draft changesets

  $ $TESTDIR/testing/bugzilla.py create-bug TestProduct TestComponent bug6

  $ hg clone -r 0 try bug-in-draft > /dev/null
  $ cd bug-in-draft
  $ echo bug-in-draft > foo
  $ hg commit -m 'Bug 5 - This should also irrelevant'
  $ hg phase --public -r .
  $ echo foo > foo
  $ hg commit -m 'Bug 6 - New draft changeset with bug'
  $ echo try > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push --force http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files (+1 heads)
  recording TBPL push in bug 6

  $ $TESTDIR/testing/bugzilla.py dump-bug 5 6
  Bug 5:
    comments:
    - id: 9
      text: ''
    summary: bug5
  Bug 6:
    comments:
    - id: 10
      text: ''
    - id: 11
      text: https://tbpl.mozilla.org/?tree=Try&rev=9257b757fa7a
    summary: bug6

  $ cd ..

  $ $TESTDIR/testing/docker-control.py stop-bmo bzpost-test-post
  stopped 2 containers
