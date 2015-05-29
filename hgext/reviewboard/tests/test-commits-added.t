#require docker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent 'Initial Bug'

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
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (visit review url to publish this review request so others can see it)

Adding commits to old reviews should create new reviews

  $ echo 'foo3' > foo
  $ hg commit -m 'Bug 1 - Foo 3'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 3 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  changeset:  3:f34b8ce40ee8
  summary:    Bug 1 - Foo 3
  review:     http://*:$HGPORT1/r/4 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (visit review url to publish this review request so others can see it)

The parent review should have its description updated.

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: false
  bugs: []
  commit: bz://1/mynick
  submitter: default+5
  summary: ''
  description: ''
  target_people: []
  extra_data:
    p2rb: true
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[2, 3, 4]'
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
    - hg pull -r f34b8ce40ee8891a60bfb98614d9ad602993a9ed http://*:$HGPORT/test-repo (glob)
    target_people: []
    extra:
      p2rb: true
      p2rb.commits: '[["24417bc94b2c053e8f5dd8c09da33fbbef5404fe", 2], ["61e2e5c813d2c6a3858a22cd8e76ece29195f87d",
        3], ["f34b8ce40ee8891a60bfb98614d9ad602993a9ed", 4]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 4
      revision: 1
      base_commit_id: 7c5bdf0cec4a90edb36300f8f3679857f46db829
      patch:
      - diff -r 7c5bdf0cec4a -r f34b8ce40ee8 foo
      - "--- a/foo\tThu Jan 01 00:00:00 1970 +0000"
      - "+++ b/foo\tThu Jan 01 00:00:00 1970 +0000"
      - '@@ -1,1 +1,1 @@'
      - -foo0
      - +foo3

Ensure we are able to deal with rids that are strings by forcing the commit
rids to be strings and then pushing a new commit.

  $ rbmanage convert-draft-rids-to-str 1
  $ echo 'foo4' > foo
  $ hg commit -m 'Bug 1 - Foo 4'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 4 changesets for review
  
  changeset:  1:24417bc94b2c
  summary:    Bug 1 - Foo 1
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:61e2e5c813d2
  summary:    Bug 1 - Foo 2
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  changeset:  3:f34b8ce40ee8
  summary:    Bug 1 - Foo 3
  review:     http://*:$HGPORT1/r/4 (draft) (glob)
  
  changeset:  4:6d1a9431c7b1
  summary:    Bug 1 - Foo 4
  review:     http://*:$HGPORT1/r/5 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (visit review url to publish this review request so others can see it)

Cleanup

  $ mozreview stop
  stopped 8 containers
