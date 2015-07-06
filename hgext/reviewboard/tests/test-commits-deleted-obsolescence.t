#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent summary

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF
  $ echo obs "obs=$TESTTMP/obs.py" >> client/.hg/hgrc

  $ cd client
  $ echo 'foo' > foo0
  $ hg commit -A -m 'root commit'
  adding foo0
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
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 5 changesets)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 5 changesets with 5 changes to 5 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 5 changesets for review
  
  changeset:  6:6bd3fbee3dfa
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  7:dfe48634934b
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  changeset:  8:d751d4c04967
  summary:    Bug 1 - Foo 3
  review:     http://*:$HGPORT1/r/4 (draft) (glob)
  
  changeset:  9:98dd6a7335db
  summary:    Bug 1 - Foo 4
  review:     http://*:$HGPORT1/r/5 (draft) (glob)
  
  changeset:  10:76088734e3cb
  summary:    Bug 1 - Foo 5
  review:     http://*:$HGPORT1/r/6 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

  $ rbmanage publish 1

Popping the last commit truncates the review set

  $ hg strip -r 76088734e3cb --no-backup
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 4 changesets for review
  
  changeset:  6:6bd3fbee3dfa
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (glob)
  
  changeset:  7:dfe48634934b
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (glob)
  
  changeset:  8:d751d4c04967
  summary:    Bug 1 - Foo 3
  review:     http://*:$HGPORT1/r/4 (glob)
  
  changeset:  9:98dd6a7335db
  summary:    Bug 1 - Foo 4
  review:     http://*:$HGPORT1/r/5 (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

Review request 6 should be in the list of review requests to discard
on publish.

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
  - /r/4 - Bug 1 - Foo 3
  - /r/5 - Bug 1 - Foo 4
  - /r/6 - Bug 1 - Foo 5
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 76088734e3cba33be80930be14e7cd1e9ee474be http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e", 2], ["dfe48634934bd5d856a937479aadf54800c242c5",
      3], ["d751d4c04967ba4ec08425f618ba8d2c1b9d161a", 4], ["98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb",
      5], ["76088734e3cba33be80930be14e7cd1e9ee474be", 6]]'
    p2rb.discard_on_publish_rids: '[6]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description:
    - /r/2 - Bug 1 - Foo 1
    - /r/3 - Bug 1 - Foo 2
    - /r/4 - Bug 1 - Foo 3
    - /r/5 - Bug 1 - Foo 4
    - ''
    - 'Pull down these commits:'
    - ''
    - hg pull -r 98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb http://*:$HGPORT/test-repo (glob)
    target_people: []
    extra:
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e", 2], ["dfe48634934bd5d856a937479aadf54800c242c5",
        3], ["d751d4c04967ba4ec08425f618ba8d2c1b9d161a", 4], ["98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb",
        5]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.reviewer_map: '{}'
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 7
      revision: 2
      base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
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

The parent review should have dropped the reference to /r/6

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
  - /r/4 - Bug 1 - Foo 3
  - /r/5 - Bug 1 - Foo 4
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e", 2], ["dfe48634934bd5d856a937479aadf54800c242c5",
      3], ["d751d4c04967ba4ec08425f618ba8d2c1b9d161a", 4], ["98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb",
      5]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'

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
    p2rb: true
    p2rb.commit_id: 76088734e3cba33be80930be14e7cd1e9ee474be
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Dropping the first commit should drop its review. Subsequent reviews should
be preserved.

  $ hg -q rebase -s dfe48634934b -d 0
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 0 changes to ? files (+1 heads) (glob)
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 3 changesets for review
  
  changeset:  10:e1679d43aceb
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  changeset:  11:13cf6665548a
  summary:    Bug 1 - Foo 3
  review:     http://*:$HGPORT1/r/4 (draft) (glob)
  
  changeset:  12:b891c874875b
  summary:    Bug 1 - Foo 4
  review:     http://*:$HGPORT1/r/5 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

Review request 2 should be in the list of review requests to discard
on publish.

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
  - /r/4 - Bug 1 - Foo 3
  - /r/5 - Bug 1 - Foo 4
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e", 2], ["dfe48634934bd5d856a937479aadf54800c242c5",
      3], ["d751d4c04967ba4ec08425f618ba8d2c1b9d161a", 4], ["98dd6a7335dbea4bd3d2f2d1662fd6db45f1ddfb",
      5]]'
    p2rb.discard_on_publish_rids: '[2]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description:
    - /r/3 - Bug 1 - Foo 2
    - /r/4 - Bug 1 - Foo 3
    - /r/5 - Bug 1 - Foo 4
    - ''
    - 'Pull down these commits:'
    - ''
    - hg pull -r b891c874875b046c191a868d55830aa201b28ebe http://*:$HGPORT/test-repo (glob)
    target_people: []
    extra:
      p2rb: true
      p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
      p2rb.commits: '[["e1679d43acebff4b173624488cdf4b5eff1ccd94", 3], ["13cf6665548ad20d8cb7eed42c3ffc1c7689939f",
        4], ["b891c874875b046c191a868d55830aa201b28ebe", 5]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.reviewer_map: '{"3": [], "2": [], "5": [], "4": []}'
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 8
      revision: 3
      base_commit_id: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
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

  $ rbmanage publish 1

The dropped commit should now be discarded

  $ rbmanage dumpreview 2
  id: 2
  status: discarded
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
    p2rb.commit_id: 6bd3fbee3dfaa83a6fe253b5a9bdc625a5d0be0e
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Try removing a commit in the middle.

  $ hg -q rebase -s b891c874875b -d e1679d43aceb
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to ? files (+1 heads) (glob)
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 2 changesets for review
  
  changeset:  10:e1679d43aceb
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (glob)
  
  changeset:  13:74896d4d6f00
  summary:    Bug 1 - Foo 4
  review:     http://*:$HGPORT1/r/5 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

  $ rbmanage publish 1

The parent review should have been updated accordingly.

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
  - /r/3 - Bug 1 - Foo 2
  - /r/5 - Bug 1 - Foo 4
  - ''
  - 'Pull down these commits:'
  - ''
  - hg pull -r 74896d4d6f00bcd490131c146eeae800e3822e0d http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.base_commit: 93d9429b41ecf0d2ad8c62b6ea26686dd20330f4
    p2rb.commits: '[["e1679d43acebff4b173624488cdf4b5eff1ccd94", 3], ["74896d4d6f00bcd490131c146eeae800e3822e0d",
      5]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{"3": [], "5": [], "4": []}'
    p2rb.unpublished_rids: '[]'

Cleanup

  $ mozreview stop
  stopped 8 containers
