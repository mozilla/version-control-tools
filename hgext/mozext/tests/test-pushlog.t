  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > 
  > [extensions]
  > mozext = $TESTDIR/hgext/mozext
  > localmozrepo = $TESTDIR/testing/local-mozilla-repos.py
  > 
  > [localmozrepo]
  > readuri = http://localhost:$HGPORT/
  > writeuri = ssh://user@dummy/$TESTTMP/
  > EOF

  $ export USER=hguser
  $ hg init mozilla-central
  $ cd mozilla-central
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ cd ..
  $ cat > hgweb.conf << EOF
  > [paths]
  > / = $TESTTMP/*
  > EOF
  $ hg serve -d -p $HGPORT --pid-file server.pid --web-conf hgweb.conf
  $ cat server.pid >> $DAEMON_PIDS

  $ hg init client
  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push ../mozilla-central
  pushing to ../mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog
  $ cd ..

Pull via http:// will fetch pushlog

  $ hg clone -U http://localhost:$HGPORT/mozilla-central clonehttp
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  added 1 pushes
  new changesets 96ee1d7354c4 (?)

Pull via ssh:// will not fetch pushlog

  $ hg clone -U ssh://user@dummy/$TESTTMP/mozilla-central clonessh
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  cannot fetch pushlog when pulling via ssh://; you should be pulling via https://
  new changesets 96ee1d7354c4 (?)
