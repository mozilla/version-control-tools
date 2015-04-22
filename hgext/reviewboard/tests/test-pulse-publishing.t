#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-bugzilla

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

Pushing a review should not publish to Pulse

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 2 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (visit review url to publish this review request so others can see it)

  $ pulse dump-messages exchange/mozreview/ all
  []

Publishing the review request will send a single message to Pulse with
details from the parent review request

  $ rbmanage publish 1
  $ pulse dump-messages exchange/mozreview/ all
  - _meta:
      exchange: exchange/mozreview/
      routing_key: mozreview.commits.published
    commits:
    - diffset_revision: 1
      rev: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
      review_request_id: 2
    - diffset_revision: 1
      rev: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
      review_request_id: 3
    parent_diffset_revision: 1
    parent_review_request_id: 1
    repository_url: http://*:$HGPORT/test-repo (glob)
    review_board_url: http://*:$HGPORT1/ (glob)

Cleanup

  $ mozreview stop
  stopped 8 containers
