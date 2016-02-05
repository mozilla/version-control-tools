#require mozreviewdocker
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
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/0050780911c8*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  3:51c15ef8210f
  summary:    h1c1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  4:b560312f6487
  summary:    h1c2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick-1
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ hg push -r . --reviewid bz://1/mynick-2
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/85811c4bd2cd*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  3:172c9543f80c
  summary:    h2c1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  changeset:  4:e8c63e38a772
  summary:    h2c2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6 (draft)
  
  review id:  bz://1/mynick-2
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

User can't remote strip unless allowed

  $ hg debugpushkey ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo strip dummy '' f5dc8e52d06801d11b624f3bf4d742240ed200e9
  remote: user not in list of users allowed to remote strip
  False
  [1]

User in whitelist can strip

  $ mozreview create-ldap-user adminuser@example.com adminuser 2002 'Admin User' --key-file ${MOZREVIEW_HOME}/keys/adminuser@example.com --scm-level 1
  $ export SSH_KEYNAME=adminuser@example.com
  $ mozreview exec hgrb /set-strip-users test-repo adminuser@example.com > /dev/null

  $ hg debugpushkey ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo strip dummy '' 51c15ef8210ffd51361c9197c85d5a4aa1bdd4a5
  remote: saved backup bundle to /repo/hg/mozilla/test-repo/.hg/strip-backup/51c15ef8210f-7eb5dc8a-remotestrip.hg
  remote: changeset will be deleted from pushlog: 51c15ef8210ffd51361c9197c85d5a4aa1bdd4a5
  remote: changeset will be deleted from pushlog: b560312f64877bf0f5261d9cd1d71e71637be899
  remote: changeset rev will be updated in pushlog: 172c9543f80cfa7f85ad5a0a6ad9b005cd18825c
  remote: changeset rev will be updated in pushlog: e8c63e38a772cd7da20caff013d5ec3f85a02fd5
  True

  $ hg -q clone ssh://${HGSSH_HOST}:${HGSSH_PORT}/test-repo new-repo
  $ hg -R new-repo log -T '{node} {desc|firstline}\n'
  e8c63e38a772cd7da20caff013d5ec3f85a02fd5 h2c2
  172c9543f80cfa7f85ad5a0a6ad9b005cd18825c h2c1
  55482a6fb4b1881fa8f746fd52cf6f096bb21c89 initial

Stripping of public changesets is disallowed

  $ hg debugpushkey ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo strip dummy '' 55482a6fb4b1881fa8f746fd52cf6f096bb21c89
  remote: cannot strip public changeset: 55482a6fb4b1881fa8f746fd52cf6f096bb21c89
  False
  [1]

Cleanup

  $ mozreview stop
  stopped 9 containers
