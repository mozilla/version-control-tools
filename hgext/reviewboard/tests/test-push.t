#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-push

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ cat >> client/.hg/hgrc << EOF
  > mq=
  > rebase=
  > EOF

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
  $ hg bookmark bookmark-2
  $ echo 'bookmark-2a' > foo
  $ hg commit -m 'bookmark with 2 commits, 1st'
  created new head
  $ echo 'bookmark-2b' > foo
  $ hg commit -m 'bookmark with 2 commits, 2nd'
  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
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
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://345/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

{reviews} template works

  $ hg log -r 0::1 --template "{node|short} {reviews % '{get(review, \"url\")} {get(review, \"status\")}'}\n"
  3a9f6899ef84 
  6f06b4ac6efe http://localhost:$HGPORT1/r/2 pending

Pushing no changesets will do a re-review

  $ hg push -r 1 --reviewid 345 http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://345/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  [1]

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
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  review id:  bz://784841/mynick
  review url: http://localhost:$HGPORT1/r/3 (pending)

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
  review:     http://localhost:$HGPORT1/r/6 (pending)
  
  review id:  bz://3452/mynick
  review url: http://localhost:$HGPORT1/r/5 (pending)
  [1]

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
  review:     http://localhost:$HGPORT1/r/8 (pending)
  
  review id:  bz://123/mynick
  review url: http://localhost:$HGPORT1/r/7 (pending)

Specifying multiple -r for the same head works

  $ hg push -r 0 -r 1 --reviewid 50000 ssh://user@dummy/$TESTTMP/server
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://localhost:$HGPORT1/r/10 (pending)
  
  review id:  bz://50000/mynick
  review url: http://localhost:$HGPORT1/r/9 (pending)
  [1]

  $ cd ..
  $ rbmanage stop rbserver
  $ dockercontrol stop-bmo rb-test-push
  stopped 2 containers
