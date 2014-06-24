  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ hg init client
  $ hg init server

  $ cat >> server/.hg/hgrc <<EOF
  > [web]
  > push_ssl = False
  > allow_push = *
  > [extensions]
  > EOF
  $ echo "reviewboard=$(echo $TESTDIR)/hgext/reviewboard/server.py" >> server/.hg/hgrc

Sserver should complain if the extension is not configured

  $ hg -R server identify
  abort: Please set reviewboard.url to the URL of the Review Board instance to talk to.
  [255]

  $ echo "[reviewboard]" >> server/.hg/hgrc
  $ echo "url = http://localhost/" >> server/.hg/hgrc
  $ hg -R server identify
  abort: Please set reviewboard.repoid to the numeric ID of the repository this repo is associated with.
  [255]

  $ echo "repoid = 1" >> server/.hg/hgrc
  $ hg -R server identify
  000000000000 tip

  $ hg serve -R server -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ cat >> client/.hg/hgrc <<EOF
  > [extensions]
  > EOF
  $ echo "reviewboard=$(echo $TESTDIR)/hgext/reviewboard/client.py" >> client/.hg/hgrc
  $ echo "[reviewboard]" >> client/.hg/hgrc

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

Attempt to push while not configured will result in a warning

  $ echo "bar" > foo
  $ hg commit -m 'second commit'
  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  tip: to not prompt for Bugzilla credentials in the future, * (glob)
  Bugzilla username None
  Bugzilla credentials not available. Not submitting review.

Configure authentication

  $ cat >> .hg/hgrc << EOF
  > [bugzilla]
  > username = user
  > password = pass
  > EOF

Unknown review identifier

  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  Unable to determine review identifier. Review identifiers are extracted * (glob)
  [1]

Bad review identifier

  $ hg push --reviewid foobar
  abort: review identifier must be a bug number.
  [255]

Pushing multiple heads is rejected

  $ echo 'head 1' > foo
  $ hg commit -m 'head 1'
  $ hg up .^
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 'head 2' > foo
  $ hg commit -m 'head 2'
  created new head
  $ hg push -r 0:tip --reviewid bz://784841 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  abort: cannot push multiple heads to remote; limit pushed revisions using the -r argument.
  [255]
