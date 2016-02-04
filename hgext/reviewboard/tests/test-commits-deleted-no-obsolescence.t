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

  $ hg push
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
  
  changeset:  1:6bd3fbee3dfa
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:dfe48634934b
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  3:d751d4c04967
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  4:98dd6a7335db
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  changeset:  5:76088734e3cb
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
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  no changes found
  submitting 4 changesets for review
  
  changeset:  1:6bd3fbee3dfa
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  2:dfe48634934b
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  3:d751d4c04967
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4
  
  changeset:  4:98dd6a7335db
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
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e", 2], ["dfe48634934bd5d856a937479aadf54800c242c5",
      3], ["d751d4c04967ba4ec08425f618ba8d2c1b9d161a", 4], ["98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb",
      5], ["76088734e3cba33be80930be14e7cd1e9ee474be", 6]]'
    p2rb.discard_on_publish_rids: '[6]'
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  commit_extra_data:
    p2rb.identifier: bz://1/mynick
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
  approval_failure: Commit 6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e is not approved.
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description: This is the parent review request
    target_people: []
    extra:
      calculated_trophies: true
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e", 2], ["dfe48634934bd5d856a937479aadf54800c242c5",
        3], ["d751d4c04967ba4ec08425f618ba8d2c1b9d161a", 4], ["98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb",
        5]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.is_squashed: true
      p2rb.reviewer_map: '{}'
      p2rb.unpublished_rids: '[]'
    commit_extra_data:
      p2rb.identifier: bz://1/mynick
    diffs:
    - id: 7
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
  description: Bug 1 - Foo 5
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: 76088734e3cba33be80930be14e7cd1e9ee474be
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.is_squashed: false
  commit_extra_data:
    p2rb.identifier: bz://1/mynick
  diffs:
  - id: 6
    revision: 1
    base_commit_id: 98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb
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

Dropping the first commit should shuffle all the reviews down the line.
NOTE: If we ever employ heuristic matching on the server, this test
likely gets invalidated.

  $ hg -q rebase -s 2 -d 0
  $ hg strip -r 1 --no-backup
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 0 changes to 3 files (+1 heads)
  remote: recorded push in pushlog
  submitting 3 changesets for review
  
  changeset:  1:7050183d97d5
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:d7a5827a584d
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  3:b5473ad606f4
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

The first commit was rewritten (we assume all subsequent were as well).

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
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: 6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.is_squashed: false
  commit_extra_data:
    p2rb.identifier: bz://1/mynick
  diffs:
  - id: 2
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
  draft:
    bugs:
    - '1'
    commit: null
    summary: Bug 1 - Foo 2
    description: Bug 1 - Foo 2
    target_people: []
    extra:
      calculated_trophies: true
      p2rb: true
      p2rb.commit_id: 7050183d97d5f601da86fb313dd8783ccf1ade18
      p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.is_squashed: false
    commit_extra_data:
      p2rb.identifier: bz://1/mynick
    diffs:
    - id: 9
      revision: 2
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
      - ''

The last review request that got invalidated in the shuffle should
be in the list of review requests to discard when the squashed review
request is published.

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
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e", 2], ["dfe48634934bd5d856a937479aadf54800c242c5",
      3], ["d751d4c04967ba4ec08425f618ba8d2c1b9d161a", 4], ["98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb",
      5]]'
    p2rb.discard_on_publish_rids: '[5]'
    p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  commit_extra_data:
    p2rb.identifier: bz://1/mynick
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
  - id: 7
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
  approval_failure: Commit 6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e is not approved.
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description: This is the parent review request
    target_people: []
    extra:
      calculated_trophies: true
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["7050183d97d5f601da86fb313dd8783ccf1ade18", 2], ["d7a5827a584db609f6a9ca2bd3d43aa3afa6b86e",
        3], ["b5473ad606f40840715d6b378dacc1a37f6263b1", 4]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.first_public_ancestor: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.is_squashed: true
      p2rb.reviewer_map: '{"3": [], "2": [], "5": [], "4": []}'
      p2rb.unpublished_rids: '[]'
    commit_extra_data:
      p2rb.identifier: bz://1/mynick
    diffs:
    - id: 8
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

  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:7050183d97d5
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  2:2fbc30f77859
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ mozreview stop
  stopped 9 containers
