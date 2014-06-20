  $ hg init client
  $ hg init server

  $ cat >> server/.hg/hgrc <<EOF
  > [web]
  > push_ssl = False
  > allow_push = *
  > [reviewboard]
  > url = http://dummy
  > repoid = 1
  > [extensions]
  > EOF
  $ echo "reviewboard=$(echo $TESTDIR)/hgext/reviewboard/server.py" >> server/.hg/hgrc

  $ cat >> client/.hg/hgrc <<EOF
  > [reviewboard]
  > username = user
  > password = pass
  > [extensions]
  > EOF
  $ echo "reviewboard=$(echo $TESTDIR)/hgext/reviewboard/client.py" >> client/.hg/hgrc

  $ hg serve -R server -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd client
  $ echo "foo" > foo
  $ hg commit -A -m 'first commit'
  adding foo
  $ hg push --noreview http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ echo "bar" > foo
  $ hg commit -m 'Bug 123 - second commit'
  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  Attempting to create a code review...
  Identified 1 changesets for review
  Review identifier: 123
  This will get printed on the client
