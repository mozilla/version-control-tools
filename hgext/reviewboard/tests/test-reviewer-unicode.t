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

Adding a reviewer with emoji in name string

  $ exportbzauth admin@example.com password
  $ bugzilla create-user uni@example.com password 'Emoji here ⌚️ :uni'
  * UnicodeWarning: * (glob)
  * (glob)
  created user 6
  $ exportbzauth default@example.com password
  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - awesome stuff; r?uni'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/9d48a700b5eb-316206f4-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:63b694541f47
  summary:    Bug 1 - awesome stuff; r?uni
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Adding a reviewer with emoji in name string who is not accepting reviews

  $ mozreview exec bmoweb /var/lib/bugzilla/bugzilla/scripts/user-prefs.pl uni@example.com set block_reviews on
  'block_reviews' set to 'on'
  $ echo foo3 > foo
  $ hg commit -m 'Bug 1 - awesome stuff again; r?uni'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:63b694541f47
  summary:    Bug 1 - awesome stuff; r?uni
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  2:7f8eef10433f
  summary:    Bug 1 - awesome stuff again; r?uni
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  error publishing review request 1: Error publishing: Bugzilla error: Emoji here ?? :uni <uni@example.com> is not currently accepting 'review' requests. (HTTP 500, API Error 225)
  (review requests not published; visit review url to attempt publishing there)

