#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Create a bug

  $ bugzilla create-bug TestProduct TestComponent 'First Bug'

Create an initial commit.

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Add some potential reviewers.

  $ mozreview create-user cthulhu@example.com password 'Cthulhu :cthulhu'
  Created user 6

We should see a warning if someone uses r= and the reviewer has not granted
a shipit.

  $ echo foo >> foo
  $ hg commit -m 'bug 1 - stuff; r=cthulhu'
  $ hg push --config reviewboard.autopublish=true
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/165ec4a3fc81-1c3847cc-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  commit message for 4b8b122bb501 has r=cthulhu but they have not granted a ship-it. review will be requested on your behalf
  
  changeset:  1:4b8b122bb501
  summary:    bug 1 - stuff; r=cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)? y
  (published review request 1)

  $ rbmanage list-reviewers 2
  cthulhu

There are no warnings for reviewers who haved granted a ship-it when using r=

  $ exportbzauth cthulhu@example.com password
  $ rbmanage create-review 2 --body-top "Ship-it!" --public --ship-it
  created review 1
  $ exportbzauth default@example.com password
  $ echo foo >> foo
  $ hg commit --amend -m "bug 1 - serious changes; r=cthulhu"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/4b8b122bb501-afed4b13-amend-backup.hg (glob)
  $ hg push --config reviewboard.autopublish=true
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:e47b87b1a589
  summary:    bug 1 - serious changes; r=cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)? y
  (published review request 1)

  $ rbmanage list-reviewers 2
  cthulhu


There are warnings for reviewers who haved granted a non ship-it review when
using r=.

  $ exportbzauth cthulhu@example.com password
  $ rbmanage create-review 2 --body-top "No way you should ship-it!" --public
  created review 2

  $ exportbzauth default@example.com password
  $ echo foo >> foo
  $ hg commit --amend -m "bug 1 - even better stuff; r=cthulhu"
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/e47b87b1a589-8fe56fc5-amend-backup.hg (glob)
  $ hg push --config reviewboard.autopublish=true
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 1 changesets for review
  commit message for b3fb18cc7421 has r=cthulhu but they have not granted a ship-it. review will be requested on your behalf
  
  changeset:  1:b3fb18cc7421
  summary:    bug 1 - even better stuff; r=cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)? y
  (published review request 1)

  $ rbmanage list-reviewers 2
  cthulhu

Cleanup

  $ mozreview stop
  stopped 9 containers
