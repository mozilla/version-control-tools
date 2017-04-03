  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > conduit-client = $TESTDIR/hgext/conduit-client/client.py
  > EOF

  $ hg init repo1
  $ cd repo1
  $ echo 'foo0' > foo
  $ hg -q commit -A -m '1st commit'

Requires a bugzilla username to be set
  $ hg conduitstage -r 0 http://localhost:77777
  abort: bugzilla username or apikey not present in .hgrc config
  (make sure that a username and apikey are set in the bugzilla section of your .hgrc config)
  [255]

Set bugzilla username
  $ cat >> $HGRCPATH << EOF
  > [bugzilla]
  > username = mozillian@example.com
  > EOF

Requires a bugzilla apikey to be set
  $ hg conduitstage -r 0 http://localhost:77777
  abort: bugzilla username or apikey not present in .hgrc config
  (make sure that a username and apikey are set in the bugzilla section of your .hgrc config)
  [255]

Set bugzilla apikey
  $ cat >> $HGRCPATH << EOF
  > apikey = fakeapikey0
  > EOF

The magic happy path works
  $ hg conduitstage -r 0 http://localhost:77777
  Publishing commits for mozillian@example.com:
  fe1507847927ea10fbd79bc4821fa4fb34ea1282

The argument order doesn't matter
  $ hg conduitstage http://localhost:77777 -r 0
  Publishing commits for mozillian@example.com:
  fe1507847927ea10fbd79bc4821fa4fb34ea1282

Add two new commits
  $ echo 'foo1' > foo
  $ hg -q commit -A -m '2nd commit'
  $ echo 'foo2' > foo
  $ hg -q commit -A -m '3rd commit'

Publishes only the given commit, no ancestors
  $ hg conduitstage -r 2 http://localhost:77777
  Publishing commits for mozillian@example.com:
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes the current commit if given '.'
  $ hg conduitstage -r . http://localhost:77777
  Publishing commits for mozillian@example.com:
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes the current commit and ancestors if -d is given, but -r is not
  $ hg conduitstage -d http://localhost:77777
  Publishing commits for mozillian@example.com:
  fe1507847927ea10fbd79bc4821fa4fb34ea1282
  372194518d2b158d172f98ec436c85e73a3625e4
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes the commit 1 and ancestors if -d is given and -r is 1
  $ hg conduitstage -d -r 1 http://localhost:77777
  Publishing commits for mozillian@example.com:
  fe1507847927ea10fbd79bc4821fa4fb34ea1282
  372194518d2b158d172f98ec436c85e73a3625e4

Publishes the commits in the revision range, entire tree
  $ hg conduitstage -r 0::2 http://localhost:77777
  Publishing commits for mozillian@example.com:
  fe1507847927ea10fbd79bc4821fa4fb34ea1282
  372194518d2b158d172f98ec436c85e73a3625e4
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes the commits in the revision range, subset of tree
  $ hg conduitstage -r 1::2 http://localhost:77777
  Publishing commits for mozillian@example.com:
  372194518d2b158d172f98ec436c85e73a3625e4
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes the commits in the correct order
  $ hg conduitstage -r 2:1 http://localhost:77777
  Publishing commits for mozillian@example.com:
  372194518d2b158d172f98ec436c85e73a3625e4
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes the commits in the revision range using full ids
  $ hg conduitstage -r fe1507847927::cb0b9488cd76 http://localhost:77777
  Publishing commits for mozillian@example.com:
  fe1507847927ea10fbd79bc4821fa4fb34ea1282
  372194518d2b158d172f98ec436c85e73a3625e4
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes only non public commits
  $ hg -q update 0
  $ hg -q phase --public -r .
  $ hg -q update 2
  $ hg conduitstage -r 0::2 http://localhost:77777
  Publishing commits for mozillian@example.com:
  372194518d2b158d172f98ec436c85e73a3625e4
  cb0b9488cd76939275b57aefa675a390c752fab2

Publishes to a given topic id
  $ hg conduitstage -r 0::2 -t test_topic_123 http://localhost:77777
  Publishing to specific topic: test_topic_123
  Publishing commits for mozillian@example.com:
  372194518d2b158d172f98ec436c85e73a3625e4
  cb0b9488cd76939275b57aefa675a390c752fab2

Aborts if neither -r or -d is given
  $ hg conduitstage http://localhost:77777
  abort: no revision specified and --drafts unset.
  (use either the --rev flag or --drafts flag)
  [255]

Aborts when entering a valid, but, empty revision set
  $ hg conduitstage -r 2::1 http://localhost:77777
  abort: valid revision set turned up empty.
  (e.g. you may have entered 10::6 which turns up empty, although 6::10 and 10:6 are both valid.)
  [255]

