  $ hg init client
  $ hg init server

  $ cat >> server/.hg/hgrc <<EOF
  > [web]
  > push_ssl = False
  > allow_push = *
  > [extensions]
  > EOF
  $ echo "reviewboard=$(echo $TESTDIR)/hgext/reviewboard/server.py" >> server/.hg/hgrc

Server should complain if the extension is not configured

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

Attempting to push multiple revs will abort immediately
  $ echo "bar" > foo
  $ hg commit -m 'second commit'
  $ hg push -r 0 -r 1 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  abort: Cannot push to a Review Board repo with multiple -r arguments. Specify a single revision - the tip revision - that you would like reviewed.
  [255]

Attempt to push while not configured will result in a warning
  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  Attempting to create a code review...
  Review Board extension not properly configured: missing authentication credentials. Please define "username" and "password" in the [reviewboard] section of your hgrc.

Pushing again will result in unclear changeset since none were transferred
  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  Attempting to create a code review...
  Unable to determine what to review. Please invoke with -r to specify what to review.
  [1]

Configure authentication
  $ echo "username = user" >> .hg/hgrc
  $ echo "password = pass" >> .hg/hgrc

Unknown review identifier
  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  Attempting to create a code review...
  Unable to determine what to review. Please invoke with -r to specify what to review.
  [1]
