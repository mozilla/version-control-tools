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

  $ hg push -r 1 --reviewid 345 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://dummy/r/2
  
  review id:  bz://345
  review url: http://dummy/r/1

{reviewurl} template works

  $ hg log -r 0::1 --template '{node|short} {reviewurl}\n'
  3a9f6899ef84 
  6f06b4ac6efe http://dummy/r/2

Pushing no changesets will do a re-review

  $ hg push -r 1 --reviewid 345 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://dummy/r/2
  
  review id:  bz://345
  review url: http://dummy/r/1
  [1]
  $ removeserverstate ../server

Pushing patches from mq will result in a warning

  $ echo 'mq patch' > foo
  $ hg qnew -m 'mq patch' -d '0 0' patch1
  $ hg push -r . --reviewid 784841 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  You are using mq to develop patches. * (glob)
  submitting 1 changesets for review
  
  changeset:  7:7458cff9569f
  summary:    mq patch
  review:     http://dummy/r/2
  
  review id:  bz://784841
  review url: http://dummy/r/1

  $ hg qpop
  popping patch1
  patch queue now empty

Custom identifier will create a new review from same changesets.

  $ hg push -r 1 --reviewid 3452 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://dummy/r/2
  
  review id:  bz://3452
  review url: http://dummy/r/3
  [1]

  $ removeserverstate ../server

SSH works

  $ hg push -r 2 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  submitting 1 changesets for review
  
  changeset:  2:a21bef69f0d4
  summary:    Bug 123 - Test identifier
  review:     http://dummy/r/2
  
  review id:  bz://123
  review url: http://dummy/r/1
  $ removeserverstate ../server

A single diff is generated properly

  $ hg up bookmark-1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (activating bookmark bookmark-1)
  $ hg push --reviewid bz://789213 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  submitting 1 changesets for review
  
  changeset:  3:afef2b530106
  summary:    bookmark with single commit
  review:     http://dummy/r/2
  
  review id:  bz://789213
  review url: http://dummy/r/1

  $ cat ../server/.hg/post_reviews
  url: http://dummy
  username: user
  password: pass
  repoid: 1
  identifier: bz://789213
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
  

  $ removeserverstate ../server

Test that multiple changesets result in parent diffs

  $ hg up bookmark-2
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (activating bookmark bookmark-2)
  $ hg push -B bookmark-2 --reviewid 567 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files (+1 heads)
  submitting 2 changesets for review
  
  changeset:  4:773ae5edc399
  summary:    bookmark with 2 commits, 1st
  review:     http://dummy/r/2
  
  changeset:  5:659bcc59ed36
  summary:    bookmark with 2 commits, 2nd
  review:     http://dummy/r/3
  
  review id:  bz://567
  review url: http://dummy/r/1
  exporting bookmark bookmark-2

  $ cat ../server/.hg/post_reviews
  url: http://dummy
  username: user
  password: pass
  repoid: 1
  identifier: bz://567
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
  

Specifying multiple -r for the same head works

  $ hg push -r 0 -r 1 --reviewid 50000 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://dummy/r/2
  
  review id:  bz://50000
  review url: http://dummy/r/4
  [1]
