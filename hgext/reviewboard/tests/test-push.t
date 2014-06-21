  $ hg init client
  $ hg init server

  $ cat >> server/.hg/hgrc <<EOF
  > [phases]
  > publish = False
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
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > [reviewboard]
  > username = user
  > password = pass
  > [extensions]
  > EOF
  $ echo "reviewboard=$(echo $TESTDIR)/hgext/reviewboard/client.py" >> client/.hg/hgrc

  $ hg serve -R server -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

Set up the repo

  $ cd client
  $ echo 'foo' > foo
  $ hg commit -A -m 'first commit'
  adding foo
  $ hg push --noreview http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

Pushing a single changeset will initiate a review against that one

  $ echo 'bar' > foo
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
  Review identifier: bug123
  This will get printed on the client

Pushing no changesets will do a review if -r is given

  $ hg push -r tip http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  Attempting to create a code review...
  Identified 1 changesets for review
  Review identifier: bug123
  This will get printed on the client
  [1]

Custom identifier works

  $ hg push -r tip --reviewid foo http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  Attempting to create a code review...
  Identified 1 changesets for review
  Review identifier: foo
  This will get printed on the client
  [1]

SSH works

  $ hg push -r tip ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  Attempting to create a code review...
  Identified 1 changesets for review
  Review identifier: bug123
  This will get printed on the client
  [1]

Active bookmark is used as identifier

  $ echo 'testing bookmark' > foo
  $ hg commit -m 'testing a bookmark'
  $ hg bookmark test-bookmark
  $ hg push ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  Attempting to create a code review...
  Identified 2 changesets for review
  Review identifier: test-bookmark
  This will get printed on the client

Deactivate bookmark and ensure identifier has reset

  $ hg phase --public -r 1
  $ hg up tip
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark test-bookmark)
  $ hg push -r tip ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  Attempting to create a code review...
  Unable to determine review identifier.* (glob)
  [1]

A non-default branch will be used as the identifier

  $ hg phase --public -r 2
  $ hg branch test-branch
  marked working directory as branch test-branch
  (branches are permanent and global, did you want a bookmark?)
  $ echo 'testing branch' > foo
  $ hg commit -m 'testing a branch'
  $ hg push --new-branch ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  Attempting to create a code review...
  Identified 1 changesets for review
  Review identifier: test-branch
  This will get printed on the client

  $ hg up default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ echo 'bar file' > bar
  $ hg commit -A -m 'added bar file'
  adding bar

Monkeypatch post_reviews and test that single diff is generated properly

  $ hg up tip
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg bookmark test-bookmark
  moving bookmark 'test-bookmark' forward from a1fab71d1635

  $ echo "server_monkeypatch = $(echo $TESTDIR)/hgext/reviewboard/tests/dummy_rbpost.py" >> ../server/.hg/hgrc
  $ hg push -r . ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  Attempting to create a code review...
  Identified 1 changesets for review
  Review identifier: test-bookmark
  This will get printed on the client
  $ cat ../server/.hg/post_reviews
  url: http://dummy
  username: user
  password: pass
  rbid: 1
  identifier: test-bookmark
  0
  d13acea7b96a
  added bar file
  diff -r a1fab71d1635 -r d13acea7b96a bar
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar file
  
  NO PARENT DIFF
  SQUASHED
  diff -r a1fab71d1635 -r d13acea7b96a bar
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar file
  

Now add another commit and verify parent and squashed diffs cover the range

  $ echo "baz file" > baz
  $ hg commit -A -m "adding baz file"
  adding baz
  $ hg push -r . ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  Attempting to create a code review...
  Identified 2 changesets for review
  Review identifier: test-bookmark
  This will get printed on the client
  $ cat ../server/.hg/post_reviews
  url: http://dummy
  username: user
  password: pass
  rbid: 1
  identifier: test-bookmark
  0
  d13acea7b96a
  added bar file
  diff -r a1fab71d1635 -r d13acea7b96a bar
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar file
  
  NO PARENT DIFF
  1
  ceb74824040a
  adding baz file
  diff -r d13acea7b96a -r ceb74824040a baz
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/baz	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +baz file
  
  diff -r a1fab71d1635 -r d13acea7b96a bar
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar file
  
  SQUASHED
  diff -r a1fab71d1635 -r ceb74824040a bar
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +bar file
  diff -r a1fab71d1635 -r ceb74824040a baz
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/baz	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +baz file
  
