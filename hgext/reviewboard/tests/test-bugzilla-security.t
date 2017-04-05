#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ mozreview create-user level1@example.com password 'Level 1 :level1' --uid 2001 --scm-level 1
  Created user 6
  $ mozreview create-user security@example.com password 'Security : security' --uid 2002 --scm-level 3 --bugzilla-group core-security
  Created user 7
  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Create a bug and make it not public

  $ bugzilla create-bug firefox general v1
  $ bugzilla update-bug-group 1 --add core-security

Push is not possible due to a confidential bug

  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Foo 1 r=level1'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/861ac87d0002-459d7e90-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  abort: bug 1 could not be accessed (we do not currently allow posting of reviews to confidential bugs)
  [255]

Push is successful after making the bug public again

  $ exportbzauth security@example.com password
  $ bugzilla update-bug-group 1 --remove core-security
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  commit message for 65ff0e3de161 has r=level1 but they have not granted a ship-it. review will be requested on your behalf
  
  changeset:  1:65ff0e3de161
  summary:    Bug 1 - Foo 1 r=level1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)
  [1]

Cleanup
  $ mozreview stop
  stopped 9 containers
