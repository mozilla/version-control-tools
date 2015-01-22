#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-commits-added

  $ bugzilla create-bug TestProduct TestComponent 'Initial Bug'

  $ cd client
  $ echo 'foo0' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg push --noreview
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ hg phase --public -r .

  $ echo 'foo1' > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo 'foo2' > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  submitting 2 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

Adding commits to old reviews should create new reviews

  $ echo 'foo3' > foo
  $ hg commit -m 'Bug 1 - Foo 3'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 3 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://localhost:$HGPORT1/r/3 (pending)
  
  changeset:  3:3e4b2ebd3703
  summary:    Bug 1 - Foo 3
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)

The parent review should have its description updated.

  $ rbmanage dumpreview $HGPORT1 1
  id: 1
  status: pending
  public: false
  bugs: []
  commit: bz://1/mynick
  summary: ''
  description: ''
  extra_data:
    p2rb: true
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '["2", "3", "4"]'
  draft:
    bugs: []
    commit: bz://1/mynick
    summary: bz://1/mynick
    description:
    - /r/2 - Bug 1 - Foo 1
    - /r/3 - Bug 1 - Foo 2
    - /r/4 - Bug 1 - Foo 3
    - ''
    - 'Pull down these commits:'
    - ''
    - hg pull -r 3e4b2ebd37030e6cce8bf557a7d4f3a8f7219a11 http://localhost:$HGPORT/
    extra:
      p2rb: true
      p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", "2"], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
        "3"], ["3e4b2ebd37030e6cce8bf557a7d4f3a8f7219a11", "4"]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 4
      revision: 1
      base_commit_id: null
      patch:
      - diff -r 7c5bdf0cec4a -r 3e4b2ebd3703 foo
      - "--- a/foo\tThu Jan 01 00:00:00 1970 +0000"
      - "+++ b/foo\tThu Jan 01 00:00:00 1970 +0000"
      - '@@ -1,1 +1,1 @@'
      - -foo0
      - +foo3

  $ cd ..
  $ rbmanage stop rbserver

  $ dockercontrol stop-bmo rb-test-commits-added
  stopped 3 containers
