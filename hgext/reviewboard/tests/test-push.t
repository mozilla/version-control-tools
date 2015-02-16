#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ cat >> client/.hg/hgrc << EOF
  > mq=
  > rebase=
  > EOF

  $ bugzilla create-bug-range TestProduct TestComponent 11
  created bugs 1 to 11

Set up the repo

  $ cd client
  $ echo 'foo' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ echo 'anonymous head' > foo
  $ hg commit -m 'anonymous head'
  $ hg up -q -r 0
  $ echo 'with parseable id' > foo
  $ hg commit -m 'Bug 4 - Test identifier'
  created new head
  $ hg up -q -r 0
  $ hg bookmark bookmark-1
  $ echo 'bookmark-1' > foo
  $ hg commit -m 'bookmark with single commit'
  created new head
  $ hg up -q -r 0
  $ hg bookmark bookmark-2
  $ echo 'bookmark-2a' > foo
  $ hg commit -m 'bookmark with 2 commits, 1st'
  created new head
  $ echo 'bookmark-2b' > foo
  $ hg commit -m 'bookmark with 2 commits, 2nd'
  $ hg up -q -r 0
  $ hg branch test-branch
  marked working directory as branch test-branch
  (branches are permanent and global, did you want a bookmark?)
  $ echo 'branch' > foo
  $ hg commit -m 'branch with single commit'
  $ hg up -q -r 0

Seed the root changeset on the server

  $ hg push -r 0 --noreview http://localhost:$HGPORT/test-repo
  pushing to http://localhost:$HGPORT/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

Pushing a single changeset will initiate a single review (no children)

  $ hg push -r 1 --reviewid 1 http://localhost:$HGPORT/test-repo
  pushing to http://localhost:$HGPORT/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

{reviews} template works

  $ hg log -r 0::1 --template "{node|short} {reviews % '{get(review, \"url\")} {get(review, \"status\")}'}\n"
  3a9f6899ef84 
  6f06b4ac6efe http://localhost:$HGPORT1/r/2 pending

Pushing no changesets will do a re-review

  $ hg push -r 1 --reviewid 1 http://localhost:$HGPORT/test-repo
  pushing to http://localhost:$HGPORT/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Pushing patches from mq will result in a warning

  $ echo 'mq patch' > foo
  $ hg qnew -m 'mq patch' -d '0 0' patch1
  $ hg push -r . --reviewid 2 http://localhost:$HGPORT/test-repo
  pushing to http://localhost:$HGPORT/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  (You are using mq to develop patches. *) (glob)
  submitting 1 changesets for review
  
  changeset:  7:7458cff9569f
  summary:    mq patch
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  review id:  bz://2/mynick
  review url: http://localhost:$HGPORT1/r/3 (pending)
  (visit review url to publish this review request so others can see it)

  $ hg qpop
  popping patch1
  patch queue now empty

Custom identifier will create a new review from same changesets.

  $ hg push -r 1 --reviewid 3 http://localhost:$HGPORT/test-repo
  pushing to http://localhost:$HGPORT/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://localhost:$HGPORT1/r/6 (pending)
  
  review id:  bz://3/mynick
  review url: http://localhost:$HGPORT1/r/5 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

SSH works

  $ hg push -r 2 ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  submitting 1 changesets for review
  
  changeset:  2:6a5e03035256
  summary:    Bug 4 - Test identifier
  review:     http://localhost:$HGPORT1/r/8 (pending)
  
  review id:  bz://4/mynick
  review url: http://localhost:$HGPORT1/r/7 (pending)
  (visit review url to publish this review request so others can see it)

Specifying multiple -r for the same head works

  $ hg push -r 0 -r 1 --reviewid 5 ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://localhost:$HGPORT1/r/10 (pending)
  
  review id:  bz://5/mynick
  review url: http://localhost:$HGPORT1/r/9 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Specifying a revision range works

  $ hg push -r 0::1 --reviewid 6 ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:6f06b4ac6efe
  summary:    anonymous head
  review:     http://localhost:$HGPORT1/r/12 (pending)
  
  review id:  bz://6/mynick
  review url: http://localhost:$HGPORT1/r/11 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Specifying a base revision limits reviewed changesets

  $ hg up -q -r 0
  $ echo ignore > foo
  $ hg -q commit -m 'Ignore this commit'
  $ echo base > foo
  $ hg commit -m 'Review base'
  $ echo middle > foo
  $ hg commit -m 'Middle commit'
  $ echo tip > foo
  $ hg commit -m 'Review tip'

  $ hg push -r 84e8a1584aad::b55f2b9937c7 --reviewid 7 ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 4 changesets with 4 changes to 1 files (+1 heads)
  submitting 3 changesets for review
  
  changeset:  8:84e8a1584aad
  summary:    Review base
  review:     http://localhost:$HGPORT1/r/14 (pending)
  
  changeset:  9:ae66c8223052
  summary:    Middle commit
  review:     http://localhost:$HGPORT1/r/15 (pending)
  
  changeset:  10:b55f2b9937c7
  summary:    Review tip
  review:     http://localhost:$HGPORT1/r/16 (pending)
  
  review id:  bz://7/mynick
  review url: http://localhost:$HGPORT1/r/13 (pending)
  (visit review url to publish this review request so others can see it)

Specifying multiple -r arguments selects base and tip

  $ hg push -r 84e8a1584aad -r b55f2b9937c7 --reviewid 8 ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 3 changesets for review
  
  changeset:  8:84e8a1584aad
  summary:    Review base
  review:     http://localhost:$HGPORT1/r/18 (pending)
  
  changeset:  9:ae66c8223052
  summary:    Middle commit
  review:     http://localhost:$HGPORT1/r/19 (pending)
  
  changeset:  10:b55f2b9937c7
  summary:    Review tip
  review:     http://localhost:$HGPORT1/r/20 (pending)
  
  review id:  bz://8/mynick
  review url: http://localhost:$HGPORT1/r/17 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Specifying multiple -r in reverse order still works

  $ hg push -r b55f2b9937c7 -r 84e8a1584aad --reviewid 9 ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 3 changesets for review
  
  changeset:  8:84e8a1584aad
  summary:    Review base
  review:     http://localhost:$HGPORT1/r/22 (pending)
  
  changeset:  9:ae66c8223052
  summary:    Middle commit
  review:     http://localhost:$HGPORT1/r/23 (pending)
  
  changeset:  10:b55f2b9937c7
  summary:    Review tip
  review:     http://localhost:$HGPORT1/r/24 (pending)
  
  review id:  bz://9/mynick
  review url: http://localhost:$HGPORT1/r/21 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

-r and -c are mutually exclusive

  $ hg push -c ae66c8223052 -r b55f2b9937c7
  abort: cannot specify both -r and -c
  [255]

-c can be used to select a single changeset to review

  $ hg push -c ae66c8223052 --reviewid 11 ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  9:ae66c8223052
  summary:    Middle commit
  review:     http://localhost:$HGPORT1/r/26 (pending)
  
  review id:  bz://11/mynick
  review url: http://localhost:$HGPORT1/r/25 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Reviewing merge commits is rejected

  $ hg up -q -r 0
  $ echo merge1 > foo
  $ hg commit -m 'Bug 1 - Merge A'
  created new head
  $ hg up -q -r 0
  $ echo merge2 > foo
  $ hg commit -m 'Bug 1 - Merge B'
  created new head
  $ hg merge --tool internal:other 63170dd88642
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg commit -m 'Bug 1 - Do merge'

  $ hg push ssh://user@dummy/$TESTTMP/repos/test-repo
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files (+1 heads)
  submitting 3 changesets for review
  abort: cannot review merge commits (b21a68e5d0e0)
  [255]

Empty changesets show a reviewboard error, not an internal server
error (Bug 1128555)
  $ hg up -q -r 0
  $ touch empty
  $ hg add empty
  $ hg commit -m "Bug 2 - Added empty file"
  created new head
  $ hg push http://localhost:$HGPORT/test-repo
  pushing to http://localhost:$HGPORT/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  submitting 1 changesets for review
  abort: reviewboard error: "105 - One or more fields had errors". please try submitting the review again. if that doesn't work, you've likely encountered a bug.
  [255]

Cleanup

  $ mozreview stop
  stopped 3 containers
