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

Extension shouldn't complain if repos are not affiliated with a review
repo

  $ hg -R server identify
  000000000000 tip

reviewboard.repobasepath will trigger validation

  $ hg --config reviewboard.repobasepath=$TESTTMP -R server identify
  abort: Please set reviewboard.repoid to the numeric ID of the repository this repo is associated with.
  [255]

  $ cat >> server/.hg/hgrc << EOF
  > [reviewboard]
  > repoid = 1
  > EOF
  $ hg -R server identify
  abort: Please set reviewboard.url to the URL of the Review Board instance to talk to.
  [255]

  $ echo "url = http://localhost/" >> server/.hg/hgrc

  $ hg -R server identify
  abort: Please set reviewboard.username to the username for priveleged communications with Review Board.
  [255]

  $ echo "username = mozreview" >> server/.hg/hgrc

  $ hg -R server identify
  abort: Please set reviewboard.password to the password for priveleged communications with Review Board.
  [255]

  $ echo "password = password" >> server/.hg/hgrc

  $ hg -R server identify
  abort: Please set bugzilla.url to the URL of the Bugzilla instance to talk to.
  [255]
  $ cat >> server/.hg/hgrc << EOF
  > [bugzilla]
  > url = http://localhost/
  > EOF

Publishing repositories should trigger error

  $ hg -R server identify
  abort: reviewboard server extension is only compatible with non-publishing repositories.
  [255]

  $ echo "[phases]" >> server/.hg/hgrc
  $ echo "publish = False" >> server/.hg/hgrc
  $ hg -R server identify
  000000000000 tip

  $ hg serve -R server -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

Pushing when we don't have the client extension installed results in warning.

  $ cd client
  $ echo initial > foo
  $ hg commit -A -m initial
  adding foo
  $ hg phase --public -r .

  $ echo foo > foo
  $ hg commit -A -m 'first commit'
  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: REVIEWBOARD: You need to have the reviewboard client extension installed in order to perform code reviews.
  remote: REVIEWBOARD: See https://hg.mozilla.org/hgcustom/version-control-tools/file/tip/hgext/reviewboard/README.rst

  $ cat >> .hg/hgrc <<EOF
  > [extensions]
  > reviewboard = $TESTDIR/hgext/reviewboard/client.py
  > 
  > [reviewboard]
  > fakeids = true
  > EOF

Pushing without IRC nick configured will result in a warning

  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  abort: you must set mozilla.ircnick in your hgrc * (glob)
  [255]

  $ cat >> .hg/hgrc << EOF
  > [mozilla]
  > ircnick = mynick
  > EOF

Attempt to push with Bugzilla not configured will result in a warning

  $ echo 'bar' > foo
  $ hg commit -m 'second commit'

  $ FIREFOX_PROFILES_DIR=$TESTTMP hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/54e4f001f1bf*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 1 changes to 1 files (+1 heads)
  Bugzilla username: None
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
  abort: review identifier must begin with bz://
  [255]

  $ hg push --reviewid bz://
  abort: review identifier must not be bz://
  [255]

  $ hg push --reviewid bz://foobar
  abort: first path component of review identifier must be a bug number
  [255]

  $ hg push --reviewid bz://1234/user/extra
  abort: unrecognized review id: bz://1234/user/extra
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
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/d7b7d7300bc6-3588c900-addcommitid.hg (glob)
  searching for changes
  abort: cannot push multiple heads to remote; limit pushed revisions using the -r argument.
  [255]

  $ cd ..

Client failing to meet server capabilities is detected

  $ cat > $TESTTMP/fakerequire.py << EOF
  > from mercurial import extensions
  > 
  > def extsetup(ui):
  >     server = extensions.find('reviewboard')
  >     assert server
  >     server.requirecaps.add('fakecapability')
  > EOF

  $ cat >> server/.hg/hgrc << EOF
  > [extensions]
  > fakerequire = $TESTTMP/fakerequire.py
  > EOF

  $ hg serve -R server -d -p $HGPORT1 --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd client
  $ hg push http://localhost:$HGPORT1
  pushing to http://localhost:$HGPORT1/
  abort: reviewboard client extension is too old to speak to this server
  (upgrade your extension by running `hg -R * pull -u`) (glob)
  [255]
