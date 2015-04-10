#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv
  $ bugzilla create-bug TestProduct TestComponent summary

  $ cd client
  $ echo 'foo0' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg push --noreview
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  $ hg phase --public -r .

  $ echo 'foo1' > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo 'foo2' > foo
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
  review:     http://*:$HGPORT1/r/2 (pending) (glob)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (pending) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (pending) (glob)
  (visit review url to publish this review request so others can see it)

  $ rbmanage publish 1

Close the squashed review request as submitted, which should close all of the
child review requests.

  $ rbmanage closesubmitted 1

Squashed review request with ID 1 should be closed as submitted...

  $ rbmanage dumpreview 1
  id: 1
  status: submitted
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Foo 1
  - /r/3 - Bug 1 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", "2"], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
      "3"]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be closed as submitted...

  $ rbmanage dumpreview 2
  id: 2
  status: submitted
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

  $ rbmanage dumpreview 3
  id: 3
  status: submitted
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Re-opening the parent review request should re-open all of the children.

  $ rbmanage reopen 1

Squashed review request with ID 1 should be re-opened...

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Foo 1
  - /r/3 - Bug 1 - Foo 2
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 61e2e5c813d2c6a3858a22cd8e76ece29195f87d http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", "2"], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
      "3"]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'

Child review request with ID 2 should be re-opened...

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description: Bug 1 - Foo 1
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 24417bc94b2c053e8f5dd8c09da33fbbef5404fe
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Child review request with ID 3 should be re-opened...

  $ rbmanage dumpreview 3
  id: 3
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description: Bug 1 - Foo 2
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 61e2e5c813d2c6a3858a22cd8e76ece29195f87d
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Cleanup

  $ mozreview stop
  stopped 8 containers
