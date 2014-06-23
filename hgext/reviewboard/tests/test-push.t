  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ hg init client
  $ hg init server
  $ serverconfig server/.hg/hgrc
  $ clientconfig client/.hg/hgrc

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ echo "server_monkeypatch = ${TESTDIR}/hgext/reviewboard/tests/dummy_rbpost.py" >> server/.hg/hgrc
  $ cat >> client/.hg/hgrc << EOF
  > mq=
  > rebase=
  > EOF

  $ hg serve -R server -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

Set up the repo

  $ cd client
  $ echo 'foo' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ echo 'anonymous head' > foo
  $ hg commit -m 'anonymous head'
  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 'with parseable id' > foo
  $ hg commit -m 'Bug 123 - Test identifier'
  created new head
  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg bookmark bookmark-1
  $ echo 'bookmark-1' > foo
  $ hg commit -m 'bookmark with single commit'
  created new head
  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bookmark-1)
  $ hg bookmark bookmark-2
  $ echo 'bookmark-2a' > foo
  $ hg commit -m 'bookmark with 2 commits, 1st'
  created new head
  $ echo 'bookmark-2b' > foo
  $ hg commit -m 'bookmark with 2 commits, 2nd'
  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bookmark-2)
  $ hg branch test-branch
  marked working directory as branch test-branch
  (branches are permanent and global, did you want a bookmark?)
  $ echo 'branch' > foo
  $ hg commit -m 'branch with single commit'
  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Seed the root changeset on the server

  $ hg push -r 0 --noreview http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

Pushing a single changeset will initiate a single review (no children)

  $ hg push -r 1 --reviewid testid http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  identified 1 changesets for review
  review identifier: testid
  created review request: 1

Pushing no changesets will do a re-review if -r is given.
Since nothing has changed, we should recycle the old review.

  $ hg push -r 1 --reviewid testid http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  identified 1 changesets for review
  review identifier: testid
  updated review request: 1
  [1]

Pushing patches from mq will result in a warning

  $ echo 'mq patch' > foo
  $ hg qnew -m 'mq patch' -d '0 0' patch1
  $ hg push -r . --reviewid mq-test http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  You are using mq to develop patches. * (glob)
  identified 1 changesets for review
  review identifier: mq-test
  created review request: 2

Custom identifier will create a new review from same changesets.
TODO should the server dedupe reviews automatically?

  $ hg push -r 1 --reviewid testid2 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  identified 1 changesets for review
  review identifier: testid2
  created review request: 3
  [1]

SSH works

  $ hg push -r 2 -f ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  identified 1 changesets for review
  review identifier: bug123
  created review request: 4

Active bookmark is used as identifier

  $ hg up bookmark-1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (activating bookmark bookmark-1)
  $ hg push -B bookmark-1 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  identified 1 changesets for review
  review identifier: bookmark-1
  created review request: 5
  exporting bookmark bookmark-1

Deactivate bookmark and ensure identifier has reset
TODO should we pick up the bookmark attached to this node?

  $ hg up -r 3
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bookmark-1)
  $ hg push -r . ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  Unable to determine review identifier.* (glob)
  [1]

A non-default branch will be used as the identifier

  $ hg up test-branch
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg push --new-branch -r . ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  identified 1 changesets for review
  review identifier: test-branch
  created review request: 6

Test that single diff is generated properly

  $ hg up bookmark-1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (activating bookmark bookmark-1)
  $ hg push -r . ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  identified 1 changesets for review
  review identifier: bookmark-1
  updated review request: 5
  [1]
  $ cat ../server/.hg/post_reviews
  url: http://dummy
  username: user
  password: pass
  rbid: 1
  identifier: bookmark-1
  0
  afef2b530106d00832a59244a852230bd88a70a7
  bookmark with single commit
  diff -r 3a9f6899ef84 -r afef2b530106 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo
  +bookmark-1
  
  NO PARENT DIFF
  SQUASHED
  diff -r 3a9f6899ef84 -r afef2b530106 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo
  +bookmark-1
  

Test that multiple changesets result in parent diffs

  $ hg up bookmark-2
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (activating bookmark bookmark-2)
  $ hg push -B bookmark-2 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files (+1 heads)
  identified 2 changesets for review
  review identifier: bookmark-2
  created review request: 7
  created changeset review: 8
  created changeset review: 9
  exporting bookmark bookmark-2
  $ cat ../server/.hg/post_reviews
  url: http://dummy
  username: user
  password: pass
  rbid: 1
  identifier: bookmark-2
  0
  773ae5edc39985853a8f396765fd5b65e951cbc4
  bookmark with 2 commits, 1st
  diff -r 3a9f6899ef84 -r 773ae5edc399 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo
  +bookmark-2a
  
  NO PARENT DIFF
  1
  659bcc59ed36f1a82f17545c97d0322b16422d5b
  bookmark with 2 commits, 2nd
  diff -r 773ae5edc399 -r 659bcc59ed36 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -bookmark-2a
  +bookmark-2b
  
  diff -r 3a9f6899ef84 -r 773ae5edc399 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo
  +bookmark-2a
  
  SQUASHED
  diff -r 3a9f6899ef84 -r 659bcc59ed36 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo
  +bookmark-2b
  

Identify successor changesets via obsolescence

  $ echo "obs=$TESTTMP/obs.py" >> .hg/hgrc
  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bookmark-2)
  $ echo 'new head' > bar
  $ hg commit -A -m 'adding new head'
  adding bar
  created new head
  $ hg phase --public -r .
  $ hg rebase -b bookmark-1 -d .
  $ hg up bookmark-1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (activating bookmark bookmark-1)
  $ hg push -B bookmark-1 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 1 changes to 1 files (+1 heads)
  updating bookmark bookmark-1
  identified 1 changesets for review
  review identifier: bookmark-1
  updated review request: 5
  exporting bookmark bookmark-1

Test pushing multiple heads is rejected

  $ hg phase --public -r .
  $ echo 'head1' > foo
  $ hg commit -m 'head1'
  $ hg up -r .^
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bookmark-1)
  $ echo 'head2' > foo
  $ hg commit -m 'head2'
  created new head

  $ hg push ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  abort: cannot push multiple heads to remote; limit pushed revisions using the -r argument.
  [255]
