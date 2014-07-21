  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bzpost = $TESTDIR/hgext/bzpost
  > localmozrepo = $TESTDIR/testing/local-mozilla-repos.py
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
  > EOF

Pushing to Try will post TBPL comment

  $ hg init try
  $ cd try
  $ cat >> .hg/hgrc << EOF
  > [phases]
  > publish = False
  > [web]
  > push_ssl = False
  > allow_push = *
  > EOF

  $ hg serve -d -p $HGPORT --pid-file hg.pid --prefix try
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ hg init client
  $ cd client
  $ touch foo
  $ hg commit -A -m 'Bug 123 - Add foo'
  adding foo
  $ echo 'foo' > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  recording TBPL push in bug 123
