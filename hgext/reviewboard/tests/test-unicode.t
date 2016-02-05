#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

  $ mozreview create-user author@example.com password 'Patch Author' --username contributor --uid 2001 --scm-level 1
  Created user 6
  $ authorkey=`mozreview create-api-key author@example.com`

Create a review request

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg --encoding utf-8 commit -m 'Bug 1 - Initial commit to review ’ こ'
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} push > /dev/null
  $ rbmanage publish 1

Add a comment with unicode

  $ rbmanage create-review 1
  created review 1

The globbing is patching over a bug in mach
  $ rbmanage create-diff-comment 1 1 foo 1 'こんにちは世界'
  * UnicodeWarning: * (glob)
  * (glob)
  created diff comment 1
  $ rbmanage publish-review 1 1
  published review 1

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: author+6
  summary: "Bug 1 - Initial commit to review \u2019 \u3053"
  description: "Bug 1 - Initial commit to review \u2019 \u3053"
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.commit_id: f03366314c7798387fcd3e367afaa6ba472feb5d
    p2rb.first_public_ancestor: 3a9f6899ef84c99841f546030b036d0124a863cf
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 2
    revision: 1
    base_commit_id: 3a9f6899ef84c99841f546030b036d0124a863cf
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,1 +1,1 @@'
    - -foo
    - +initial
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: author@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: "MozReview Request: Bug 1 - Initial commit to review \u2019 \u3053"
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: "MozReview Request: Bug 1 - Initial commit to review \u2019 \u3053"
    blocks: []
    cc: []
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags: []
      text:
      - Created attachment 1
      - "MozReview Request: Bug 1 - Initial commit to review \u2019 \u3053"
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: author@example.com
      id: 3
      tags: []
      text:
      - http://$DOCKER_HOSTNAME:$HGPORT1/r/1/#review1
      - ''
      - '::: foo:1'
      - (Diff revision 1)
      - '> -foo'
      - '> +initial'
      - ''
      - "\u3053\u3093\u306B\u3061\u306F\u4E16\u754C"
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: UNCONFIRMED
    summary: First Bug

Cleanup

  $ mozreview stop
  stopped 9 containers
