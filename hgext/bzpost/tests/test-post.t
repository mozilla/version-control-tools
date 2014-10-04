#require docker
  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bzpost = $TESTDIR/hgext/bzpost
  > localmozrepo = $TESTDIR/testing/local-mozilla-repos.py
  > strip =
  > 
  > [localmozrepo]
  > readuri = http://localhost:$HGPORT/
  > writeuri = http://localhost:$HGPORT/
  > execfile = $TESTDIR/hgext/bzpost/tests/mocks.py
  > 
  > [bugzilla]
  > username = bzpost
  > password = pass
  > url = http://localhost:$HGPORT1/rest
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

Pushing to mozilla-inbound will result in bug being updated

  $ hg clone mozilla-central mi-push > /dev/null
  $ cd mi-push
  $ echo mc > foo
  $ hg commit -m 'Bug 123 - Commit to inbound'
  $ hg push http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  recording push in bug 123
    posting to bug 123
    http://localhost:$HGPORT/integration/mozilla-inbound/rev/9a3a9dc65e0c

Pushing multiple changesets with multiple bugs will result in bug being updated

  $ echo 123_1 > foo
  $ hg commit -m 'Bug 123 - First commit'
  $ echo 123_2 > foo
  $ hg commit -m 'Bug 123 - Second commit'
  $ echo 124 > foo
  $ hg commit -m 'Bug 124 - Another bug'
  $ hg push http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  recording push in bug 123
    posting to bug 123
    http://localhost:$HGPORT/integration/mozilla-inbound/rev/367c48b06fa4
    http://localhost:$HGPORT/integration/mozilla-inbound/rev/cab85a829a07
  recording push in bug 124
    posting to bug 124
    http://localhost:$HGPORT/integration/mozilla-inbound/rev/fe933515feb9

  $ cd ..


Pushing to Try will post TBPL comment

  $ hg clone -r 0 try client > /dev/null
  $ cd client
  $ echo expected > foo
  $ hg commit -m 'Bug 123 - Add foo'
  $ echo foo > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  recording TBPL push in bug 123
    posting to bug 123
    https://tbpl.mozilla.org/?tree=Try&rev=8983bb580615

  $ cd ..

Public changesets pushed to Try will be ignored if no bug in draft changesets

  $ hg clone -r 0 try no-bug-in-draft > /dev/null
  $ cd no-bug-in-draft
  $ echo no-bug-in-draft > foo
  $ hg commit -m 'Bug 500 - This should be irrelevant'
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

  $ cd ..

Public changesets pushed to Try will be ignored if a bug in draft changesets

  $ hg clone -r 0 try bug-in-draft > /dev/null
  $ cd bug-in-draft
  $ echo bug-in-draft > foo
  $ hg commit -m 'Bug 501 - This should also irrelevant'
  $ hg phase --public -r .
  $ echo foo > foo
  $ hg commit -m 'Bug 123 - New draft changeset with bug'
  $ echo try > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push --force http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files (+1 heads)
  recording TBPL push in bug 123
    posting to bug 123
    https://tbpl.mozilla.org/?tree=Try&rev=8ddc73283ce3

  $ cd ..
