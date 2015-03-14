#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

debugpushkey doesn't inherit this setting from the host repo so define it
globally

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > EOF

  $ bugzilla create-bug TestProduct TestComponent 1

  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg phase --public -r .

  $ echo h1c1 > foo
  $ hg commit -m h1c1
  $ echo h1c2 > foo
  $ hg commit -m h1c2
  $ hg -q up -r 0
  $ echo h2c1 > foo
  $ hg commit -m h2c1
  created new head
  $ echo h2c2 > foo
  $ hg commit -m h2c2

  $ hg log -T '{node} {desc}\n'
  85811c4bd2cd093cee28e98e7bb7a641965bf889 h2c2
  faaa0821e83d9b1c7070b1e458a809a79173579c h2c1
  0050780911c81eed28216c404bc64e6ecdab9a54 h1c2
  cd04635afb3cc9f4d8b8d074465a7e3d0d70908e h1c1
  55482a6fb4b1881fa8f746fd52cf6f096bb21c89 initial

  $ hg push -r 2 --reviewid bz://1/mynick-1
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  submitting 2 changesets for review
  
  changeset:  1:cd04635afb3c
  summary:    h1c1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:0050780911c8
  summary:    h1c2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://1/mynick-1
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

  $ hg push -r . --reviewid bz://1/mynick-2
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files (+1 heads)
  submitting 2 changesets for review
  
  changeset:  3:faaa0821e83d
  summary:    h2c1
  review:     http://localhost:$HGPORT1/r/5 (pending)
  
  changeset:  4:85811c4bd2cd
  summary:    h2c2
  review:     http://localhost:$HGPORT1/r/6 (pending)
  
  review id:  bz://1/mynick-2
  review url: http://localhost:$HGPORT1/r/4 (pending)
  (visit review url to publish this review request so others can see it)

User can't remote strip unless allowed

  $ hg debugpushkey ssh://user@dummy/$TESTTMP/repos/test-repo strip dummy '' faaa0821e83d9b1c7070b1e458a809a79173579c
  remote: user not in list of users allowed to remote strip
  False
  [1]

User in whitelist can strip

  $ cat >> $TESTTMP/repos/test-repo/.hg/hgrc << EOF
  > remote_strip_users = admin
  > EOF

  $ USER=admin hg debugpushkey ssh://user@dummy/$TESTTMP/repos/test-repo strip dummy '' cd04635afb3cc9f4d8b8d074465a7e3d0d70908e
  remote: saved backup bundle to $TESTTMP/repos/test-repo/.hg/strip-backup/cd04635afb3c-*remotestrip.hg (glob)
  True

  $ hg -R $TESTTMP/repos/test-repo log -T '{node} {desc}\n'
  85811c4bd2cd093cee28e98e7bb7a641965bf889 h2c2
  faaa0821e83d9b1c7070b1e458a809a79173579c h2c1
  55482a6fb4b1881fa8f746fd52cf6f096bb21c89 initial

Stripping of public changesets is disallowed

  $ USER=admin hg debugpushkey ssh://user@dummy/$TESTTMP/repos/test-repo strip dummy '' 55482a6fb4b1881fa8f746fd52cf6f096bb21c89
  remote: cannot strip public changeset: 55482a6fb4b1881fa8f746fd52cf6f096bb21c89
  False
  [1]

Cleanup

  $ mozreview stop
  stopped 6 containers
