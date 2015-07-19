#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

  $ mozreview create-user author@example.com password 'Some Contributor' --username contributor --uid 2001 --scm-level 1
  Created user 6

Create a review request from a regular user

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'

  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com push > /dev/null

Attempting to publish a commit review request should fail.

  $ rbmanage publish 2
  API Error: 500: 225: Error publishing the review request: Publishing commit review requests is prohibited, please publish parent.
  [1]

Publishing the parent should succeed.

  $ rbmanage publish 1

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: author+6
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Initial commit to review
  - ''
  - 'Pull down this commit:'
  - ''
  - hg pull -r 86a712c7f0187fed4c00b99131838610c76e6cc0 http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.base_commit: 3a9f6899ef84c99841f546030b036d0124a863cf
    p2rb.commits: '[["86a712c7f0187fed4c00b99131838610c76e6cc0", 2]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{"2": []}'
    p2rb.unpublished_rids: '[]'

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: author+6
  summary: Bug 1 - Initial commit to review
  description: Bug 1 - Initial commit to review
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 86a712c7f0187fed4c00b99131838610c76e6cc0
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

  $ cd ..

Cleanup

  $ mozreview stop
  stopped 8 containers
