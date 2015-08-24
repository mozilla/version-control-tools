#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

debugpushkey doesn't inherit this setting from the host repo so define it
globally

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = $TESTDIR/testing/mozreview-ssh
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
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/0050780911c8*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  3:f5dc8e52d068
  summary:    h1c1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  4:ad01e35ad0d8
  summary:    h1c2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick-1
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

  $ hg push -r . --reviewid bz://1/mynick-2
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/85811c4bd2cd*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  3:d03da7877f4b
  summary:    h2c1
  review:     http://*:$HGPORT1/r/5 (draft) (glob)
  
  changeset:  4:d9181bb0ade7
  summary:    h2c2
  review:     http://*:$HGPORT1/r/6 (draft) (glob)
  
  review id:  bz://1/mynick-2
  review url: http://*:$HGPORT1/r/4 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

User can't remote strip unless allowed

  $ hg debugpushkey ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo strip dummy '' f5dc8e52d06801d11b624f3bf4d742240ed200e9
  remote: user not in list of users allowed to remote strip
  False
  [1]

User in whitelist can strip

  $ mozreview create-ldap-user adminuser@example.com adminuser 2002 'Admin User' --key-file ${MOZREVIEW_HOME}/keys/adminuser@example.com --scm-level 1
  $ export SSH_KEYNAME=adminuser@example.com
  $ mozreview exec hgrb /set-strip-users test-repo adminuser@example.com > /dev/null

  $ hg debugpushkey ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo strip dummy '' f5dc8e52d06801d11b624f3bf4d742240ed200e9 
  remote: saved backup bundle to /repo/hg/mozilla/test-repo/.hg/strip-backup/f5dc8e52d068*-remotestrip.hg (glob)
  remote: changeset will be deleted from pushlog: f5dc8e52d06801d11b624f3bf4d742240ed200e9
  remote: changeset will be deleted from pushlog: ad01e35ad0d8dad239748349dfe96c16914cc37b
  remote: changeset rev will be updated in pushlog: d03da7877f4b0533ede2b5e2cc8a0d4816e6d9b1
  remote: changeset rev will be updated in pushlog: d9181bb0ade7f2362db2f6a195642148c2d48820
  True

  $ hg -q clone ssh://${HGSSH_HOST}:${HGSSH_PORT}/test-repo new-repo
  $ hg -R new-repo log -T '{node} {desc}\n'
  d9181bb0ade7f2362db2f6a195642148c2d48820 h2c2
  d03da7877f4b0533ede2b5e2cc8a0d4816e6d9b1 h2c1
  55482a6fb4b1881fa8f746fd52cf6f096bb21c89 initial

Stripping of public changesets is disallowed

  $ hg debugpushkey ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo strip dummy '' 55482a6fb4b1881fa8f746fd52cf6f096bb21c89
  remote: cannot strip public changeset: 55482a6fb4b1881fa8f746fd52cf6f096bb21c89
  False
  [1]

Cleanup

  $ mozreview stop
  stopped 8 containers
