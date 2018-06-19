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
  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} --config reviewboard.autopublish=false push > /dev/null 2>&1
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
  description:
  - "Bug 1 - Initial commit to review \u2019 \u3053"
  - ''
  - 'MozReview-Commit-ID: 124Bxg'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test
    p2rb.commit_id: 86ab97a5dd61e8ec7ff3c23212db732e3531af01
    p2rb.commit_message_filediff_ids: '{"1": 2}'
    p2rb.commit_message_filename: commit-message-3a9f6
    p2rb.first_public_ancestor: 3a9f6899ef84c99841f546030b036d0124a863cf
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 3
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
      description: "Bug 1 - Initial commit to review \u2019 \u3053"
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: "Bug 1 - Initial commit to review \u2019 \u3053"
    blocks: []
    cc: []
    comments:
    - author: author@example.com
      id: 1
      tags: []
      text: ''
    - author: author@example.com
      id: 2
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - "Bug 1 - Initial commit to review \u2019 \u3053"
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: author@example.com
      id: 3
      tags:
      - mozreview-review
      text:
      - Comment on attachment 1
      - "Bug 1 - Initial commit to review \u2019 \u3053"
      - ''
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

Put some wonky byte sequences in the diff

  $ bugzilla create-bug TestProduct TestComponent 'Bug 2'
  >>> with open('foo', 'wb') as fh:
  ...     fh.write(b'hello world \xff\xff\x7e\n')
  $ hg commit -m 'Bug 2 - base'

こんにちは世界 from above

  >>> with open('foo', 'wb') as fh:
  ...     fh.write(b'hello world \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf\xe4\xb8\x96\xe7\x95\x8c\n')
  $ hg commit -m 'Bug 2 - tip'

  $ hg --config bugzilla.username=author@example.com --config bugzilla.apikey=${authorkey} --config reviewboard.autopublish=false push -r 2::
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/3aef4f4bb0d9-c7f01cb3-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  2:78025579528e
  summary:    Bug 2 - base
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  3:6204fc917b21
  summary:    Bug 2 - tip
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  review id:  bz://2/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage dumpreview 4
  id: 4
  status: pending
  public: false
  bugs: []
  commit: null
  submitter: author+6
  summary: ''
  description: ''
  target_people: []
  extra_data: {}
  commit_extra_data:
    p2rb: true
    p2rb.commit_message_filename: commit-message-86ab9
    p2rb.identifier: bz://2/mynick
    p2rb.is_squashed: false
  diffs: []
  approved: false
  approval_failure: The review request is not public.
  draft:
    bugs:
    - '2'
    commit: null
    summary: Bug 2 - base
    description:
    - Bug 2 - base
    - ''
    - 'MozReview-Commit-ID: 5ijR9k'
    target_people: []
    extra: {}
    commit_extra_data:
      p2rb: true
      p2rb.author: test
      p2rb.commit_id: 78025579528e119adf8ccc61727fccc1e23bda1c
      p2rb.commit_message_filediff_ids: '{"1": 5}'
      p2rb.first_public_ancestor: 3a9f6899ef84c99841f546030b036d0124a863cf
      p2rb.identifier: bz://2/mynick
      p2rb.is_squashed: false
    diffs:
    - id: 5
      revision: 1
      base_commit_id: 86ab97a5dd61e8ec7ff3c23212db732e3531af01
      name: diff
      extra: {}
      patch:
      - diff --git a/commit-message-86ab9 b/commit-message-86ab9
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/commit-message-86ab9
      - '@@ -0,0 +1,3 @@'
      - +Bug 2 - base
      - +
      - '+MozReview-Commit-ID: 5ijR9k'
      - diff --git a/foo b/foo
      - '--- a/foo'
      - +++ b/foo
      - '@@ -1,1 +1,1 @@'
      - -initial
      - !!binary |
        K2hlbGxvIHdvcmxkIP//fg==
      - ''

  $ rbmanage dumpreview 5
  id: 5
  status: pending
  public: false
  bugs: []
  commit: null
  submitter: author+6
  summary: ''
  description: ''
  target_people: []
  extra_data: {}
  commit_extra_data:
    p2rb: true
    p2rb.commit_message_filename: commit-message-78025
    p2rb.identifier: bz://2/mynick
    p2rb.is_squashed: false
  diffs: []
  approved: false
  approval_failure: The review request is not public.
  draft:
    bugs:
    - '2'
    commit: null
    summary: Bug 2 - tip
    description:
    - Bug 2 - tip
    - ''
    - 'MozReview-Commit-ID: APOgLo'
    target_people: []
    extra: {}
    commit_extra_data:
      p2rb: true
      p2rb.author: test
      p2rb.commit_id: 6204fc917b213cf88051df32860d62ca91ae1422
      p2rb.commit_message_filediff_ids: '{"1": 7}'
      p2rb.first_public_ancestor: 3a9f6899ef84c99841f546030b036d0124a863cf
      p2rb.identifier: bz://2/mynick
      p2rb.is_squashed: false
    diffs:
    - id: 6
      revision: 1
      base_commit_id: 78025579528e119adf8ccc61727fccc1e23bda1c
      name: diff
      extra: {}
      patch:
      - diff --git a/commit-message-78025 b/commit-message-78025
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/commit-message-78025
      - '@@ -0,0 +1,3 @@'
      - +Bug 2 - tip
      - +
      - '+MozReview-Commit-ID: APOgLo'
      - diff --git a/foo b/foo
      - '--- a/foo'
      - +++ b/foo
      - '@@ -1,1 +1,1 @@'
      - !!binary |
        LWhlbGxvIHdvcmxkIP//fg==
      - "+hello world \u3053\u3093\u306B\u3061\u306F\u4E16\u754C"
      - ''

The raw diff demonstrates the original bytes are preserved

  $ rbmanage dump-raw-diff 4
  ID: 5 (draft)
  diff --git a/commit-message-86ab9 b/commit-message-86ab9
  new file mode 100644
  --- /dev/null
  +++ b/commit-message-86ab9
  @@ -0,0 +1,3 @@
  +Bug 2 - base
  +
  +MozReview-Commit-ID: 5ijR9k
  diff --git a/foo b/foo
  --- a/foo
  +++ b/foo
  @@ -1,1 +1,1 @@
  -initial
  +hello world \xff\xff~ (esc)
  
  

  $ rbmanage dump-raw-diff 5
  ID: 6 (draft)
  diff --git a/commit-message-78025 b/commit-message-78025
  new file mode 100644
  --- /dev/null
  +++ b/commit-message-78025
  @@ -0,0 +1,3 @@
  +Bug 2 - tip
  +
  +MozReview-Commit-ID: APOgLo
  diff --git a/foo b/foo
  --- a/foo
  +++ b/foo
  @@ -1,1 +1,1 @@
  -hello world \xff\xff~ (esc)
  +hello world \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf\xe4\xb8\x96\xe7\x95\x8c (esc)
  
  

Cleanup

  $ mozreview stop
  stopped 7 containers
