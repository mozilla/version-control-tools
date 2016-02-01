#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent 'Initial Bug'

  $ cd client
  $ echo 'foo0' > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg push --noreview
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  $ hg phase --public -r .

  $ echo 'foo1' > foo
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo 'foo2' > foo
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/61e2e5c813d2*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:a92d53c0ffc7
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:233b570e5356
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

Adding commits to old reviews should create new reviews

  $ echo 'foo3' > foo
  $ hg commit -m 'Bug 1 - Foo 3'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 3 changesets for review
  
  changeset:  1:a92d53c0ffc7
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:233b570e5356
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  3:4cb601f74de5
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

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
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[2, 3, 4]'
  diffs: []
  approved: false
  approval_failure: The review request is not public.
  draft:
    bugs:
    - '1'
    commit: bz://1/mynick
    summary: bz://1/mynick
    description: This is the parent review request
    target_people: []
    extra:
      p2rb: true
      p2rb.base_commit: 7c5bdf0cec4a90edb36300f8f3679857f46db829
      p2rb.commits: '[["a92d53c0ffc7df0517397a77980e62332552d812", 2], ["233b570e5356d0c84bcbf0633de446172012b3b3",
        3], ["4cb601f74de529935048816623637fb0ca2812a4", 4]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.reviewer_map: '{"3": [], "2": []}'
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 4
      revision: 1
      base_commit_id: 7c5bdf0cec4a90edb36300f8f3679857f46db829
      name: diff
      extra: {}
      patch:
      - diff --git a/foo b/foo
      - '--- a/foo'
      - +++ b/foo
      - '@@ -1,1 +1,1 @@'
      - -foo0
      - +foo3
      - ''

Ensure we are able to deal with rids that are strings by forcing the commit
rids to be strings and then pushing a new commit.

  $ rbmanage convert-draft-rids-to-str 1
  $ echo 'foo4' > foo
  $ hg commit -m 'Bug 1 - Foo 4'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 4 changesets for review
  
  changeset:  1:a92d53c0ffc7
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:233b570e5356
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  3:4cb601f74de5
  summary:    Bug 1 - Foo 3
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  4:fea02e8114c8
  summary:    Bug 1 - Foo 4
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

Cleanup

  $ mozreview stop
  stopped 10 containers
