#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent summary

  $ cd client
  $ echo 'foo' > foo0
  $ hg commit -A -m 'root commit'
  adding foo0
  $ hg push --noreview
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  $ hg phase --public -r .

  $ echo 'foo1' > foo1
  $ hg commit -A -m 'Bug 1 - Foo 1'
  adding foo1
  $ echo 'foo2' > foo2
  $ hg commit -A -m 'Bug 1 - Foo 2'
  adding foo2
  $ echo 'foo3' > foo3
  $ hg commit -A -m 'Bug 1 - Foo 3'
  adding foo3
  $ echo 'foo4' > foo4
  $ hg commit -A -m 'Bug 1 - Foo 4'
  adding foo4
  $ echo 'foo5' > foo5
  $ hg commit -A -m 'Bug 1 - Foo 5'
  adding foo5

  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 5 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/d86c61a23fc8*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 5 changesets with 5 changes to 5 files
  remote: recorded push in pushlog
  submitting 5 changesets for review
  
  changeset:  1:0b3e14fe3ff1
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:bce658a3f6d6
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  3:713878e22d95
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  4:4d0f846364eb
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  changeset:  5:4e50148c492d
  summary:    Bug 1 - Foo 5
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage publish 1

Popping the last commit truncates the review set

  $ hg strip -r 5 --no-backup
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  no changes found
  submitting 4 changesets for review
  
  changeset:  1:0b3e14fe3ff1
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  2:bce658a3f6d6
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  3:713878e22d95
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4
  
  changeset:  4:4d0f846364eb
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)
  [1]

Review request 6 should be added to the list of discard on publish rids.

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb.reviewer_map: '{}'
  commit_extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["0b3e14fe3ff19019110705e72dcf563c0ef551f6", 2], ["bce658a3f6d6aa04bf5c449e0e779e839de4690e",
      3], ["713878e22d952d478e88bfdef897fdfc73060351", 4], ["4d0f846364eb509a1b6ae3294f05439101f6e7d3",
      5], ["4e50148c492dde95397cd666f2d4e4ad4fd2176f", 6]]'
    p2rb.discard_on_publish_rids: '[6]'
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.has_commit_message_filediff: true
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - diff --git a/foo5 b/foo5
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo5
    - '@@ -0,0 +1,1 @@'
    - +foo5
    - ''
  approved: false
  approval_failure: Commit 0b3e14fe3ff19019110705e72dcf563c0ef551f6 is not approved.
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description: This is the parent review request
    target_people: []
    extra:
      calculated_trophies: true
      p2rb.reviewer_map: '{}'
    commit_extra_data:
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["0b3e14fe3ff19019110705e72dcf563c0ef551f6", 2], ["bce658a3f6d6aa04bf5c449e0e779e839de4690e",
        3], ["713878e22d952d478e88bfdef897fdfc73060351", 4], ["4d0f846364eb509a1b6ae3294f05439101f6e7d3",
        5]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.has_commit_message_filediff: true
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 8
      revision: 2
      base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      name: diff
      extra: {}
      patch:
      - diff --git a/foo1 b/foo1
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo1
      - '@@ -0,0 +1,1 @@'
      - +foo1
      - diff --git a/foo2 b/foo2
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo2
      - '@@ -0,0 +1,1 @@'
      - +foo2
      - diff --git a/foo3 b/foo3
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo3
      - '@@ -0,0 +1,1 @@'
      - +foo3
      - diff --git a/foo4 b/foo4
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo4
      - '@@ -0,0 +1,1 @@'
      - +foo4
      - ''

  $ rbmanage publish 1

Review 6 should be marked as discarded

  $ rbmanage dumpreview 6
  id: 6
  status: discarded
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 5
  description:
  - Bug 1 - Foo 5
  - ''
  - 'MozReview-Commit-ID: JmjAjw'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test
    p2rb.commit_id: 4e50148c492dde95397cd666f2d4e4ad4fd2176f
    p2rb.commit_message_filediff_ids: '{"1": 14}'
    p2rb.commit_message_filename: commit-message-4d0f8
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 7
    revision: 1
    base_commit_id: 4d0f846364eb509a1b6ae3294f05439101f6e7d3
    name: diff
    extra: {}
    patch:
    - diff --git a/foo5 b/foo5
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo5
    - '@@ -0,0 +1,1 @@'
    - +foo5
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Dropping the first commit should have no effect since commit ids map to
appropriate review requests

  $ hg -q rebase -s 2 -d 0
  $ hg strip -r 1 --no-backup
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 0 changes to 3 files (+1 heads)
  remote: recorded push in pushlog
  submitting 3 changesets for review
  
  changeset:  1:eeb6d49dcb09
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  2:607f375f35c0
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  3:81ee86efd38f
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

The review request corresponding to the dropped commit has no draft

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description:
  - Bug 1 - Foo 1
  - ''
  - 'MozReview-Commit-ID: 124Bxg'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test
    p2rb.commit_id: 0b3e14fe3ff19019110705e72dcf563c0ef551f6
    p2rb.commit_message_filediff_ids: '{"1": 6}'
    p2rb.commit_message_filename: commit-message-93d94
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 3
    revision: 1
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Review request 2 should be marked as discard on publish

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb.reviewer_map: '{}'
  commit_extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["0b3e14fe3ff19019110705e72dcf563c0ef551f6", 2], ["bce658a3f6d6aa04bf5c449e0e779e839de4690e",
      3], ["713878e22d952d478e88bfdef897fdfc73060351", 4], ["4d0f846364eb509a1b6ae3294f05439101f6e7d3",
      5]]'
    p2rb.discard_on_publish_rids: '[2]'
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.has_commit_message_filediff: true
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - diff --git a/foo5 b/foo5
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo5
    - '@@ -0,0 +1,1 @@'
    - +foo5
    - ''
  - id: 8
    revision: 2
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - ''
  approved: false
  approval_failure: Commit 0b3e14fe3ff19019110705e72dcf563c0ef551f6 is not approved.
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description: This is the parent review request
    target_people: []
    extra:
      calculated_trophies: true
      p2rb.reviewer_map: '{"3": [], "2": [], "5": [], "4": []}'
    commit_extra_data:
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["eeb6d49dcb0950d771959358f662cf2e5ddc9dc1", 3], ["607f375f35c0866a8e08bc1d6aaecc6ad259ed6e",
        4], ["81ee86efd38ff60717aeeeff153292e84e58be0b", 5]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.has_commit_message_filediff: true
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 9
      revision: 3
      base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      name: diff
      extra: {}
      patch:
      - diff --git a/foo2 b/foo2
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo2
      - '@@ -0,0 +1,1 @@'
      - +foo2
      - diff --git a/foo3 b/foo3
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo3
      - '@@ -0,0 +1,1 @@'
      - +foo3
      - diff --git a/foo4 b/foo4
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo4
      - '@@ -0,0 +1,1 @@'
      - +foo4
      - ''

Publish to get us up to date, but we're not going to test the publishing
behaviour here. We'll save that for other tests.

  $ rbmanage publish 1

Try removing a commit in the middle.

  $ hg -q rebase -s 3 -d 1
  $ hg strip -r 2 --no-backup

  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:eeb6d49dcb09
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  2:a27a94c54524
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

The parent review should have been updated accordingly

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb.reviewer_map: '{"3": [], "2": [], "5": [], "4": []}'
  commit_extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["eeb6d49dcb0950d771959358f662cf2e5ddc9dc1", 3], ["607f375f35c0866a8e08bc1d6aaecc6ad259ed6e",
      4], ["81ee86efd38ff60717aeeeff153292e84e58be0b", 5]]'
    p2rb.discard_on_publish_rids: '[4]'
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.has_commit_message_filediff: true
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - diff --git a/foo5 b/foo5
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo5
    - '@@ -0,0 +1,1 @@'
    - +foo5
    - ''
  - id: 8
    revision: 2
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - ''
  - id: 9
    revision: 3
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - ''
  approved: false
  approval_failure: Commit eeb6d49dcb0950d771959358f662cf2e5ddc9dc1 is not approved.
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description: This is the parent review request
    target_people: []
    extra:
      calculated_trophies: true
      p2rb.reviewer_map: '{"3": [], "5": [], "4": []}'
    commit_extra_data:
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["eeb6d49dcb0950d771959358f662cf2e5ddc9dc1", 3], ["a27a94c54524d4331dec2f92f647067bfd6dfbd4",
        5]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.has_commit_message_filediff: true
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 13
      revision: 4
      base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      name: diff
      extra: {}
      patch:
      - diff --git a/foo2 b/foo2
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo2
      - '@@ -0,0 +1,1 @@'
      - +foo2
      - diff --git a/foo4 b/foo4
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo4
      - '@@ -0,0 +1,1 @@'
      - +foo4
      - ''

Deleting a commit and adding a commit will recycle a review request
because of an unclaimed review request
TODO this is sub-optimal. We should consider changing the review request
recycling behavior when commit IDs are present.

  $ hg -q up eeb6d49dcb09

  $ echo foo6 > foo6
  $ hg -q commit -A -m 'Bug 1 - Foo 6'
  $ hg --config reviewboard.autopublish=false push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/abb8d26c0311-418bd058-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:eeb6d49dcb09
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  3:3b99865d1bab
  summary:    Bug 1 - Foo 6
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb.reviewer_map: '{"3": [], "2": [], "5": [], "4": []}'
  commit_extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["eeb6d49dcb0950d771959358f662cf2e5ddc9dc1", 3], ["607f375f35c0866a8e08bc1d6aaecc6ad259ed6e",
      4], ["81ee86efd38ff60717aeeeff153292e84e58be0b", 5]]'
    p2rb.discard_on_publish_rids: '[5]'
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.has_commit_message_filediff: true
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - diff --git a/foo5 b/foo5
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo5
    - '@@ -0,0 +1,1 @@'
    - +foo5
    - ''
  - id: 8
    revision: 2
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - ''
  - id: 9
    revision: 3
    base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    name: diff
    extra: {}
    patch:
    - diff --git a/foo2 b/foo2
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo2
    - '@@ -0,0 +1,1 @@'
    - +foo2
    - diff --git a/foo3 b/foo3
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo3
    - '@@ -0,0 +1,1 @@'
    - +foo3
    - diff --git a/foo4 b/foo4
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo4
    - '@@ -0,0 +1,1 @@'
    - +foo4
    - ''
  approved: false
  approval_failure: Commit eeb6d49dcb0950d771959358f662cf2e5ddc9dc1 is not approved.
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description: This is the parent review request
    target_people: []
    extra:
      calculated_trophies: true
      p2rb.reviewer_map: '{"3": [], "5": []}'
    commit_extra_data:
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["eeb6d49dcb0950d771959358f662cf2e5ddc9dc1", 3], ["3b99865d1bab8480235d913f4bcfc951fd9e3032",
        4]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.has_commit_message_filediff: true
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 15
      revision: 4
      base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      name: diff
      extra: {}
      patch:
      - diff --git a/foo2 b/foo2
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo2
      - '@@ -0,0 +1,1 @@'
      - +foo2
      - diff --git a/foo6 b/foo6
      - new file mode 100644
      - '--- /dev/null'
      - +++ b/foo6
      - '@@ -0,0 +1,1 @@'
      - +foo6
      - ''

  $ mozreview stop
  stopped 7 containers
