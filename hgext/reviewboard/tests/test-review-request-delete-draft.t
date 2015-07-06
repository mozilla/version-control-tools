#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ adminbugzilla create-user submitter@example.com password 'Dummy Submitter'
  created user 6
  $ mozreview create-ldap-user submitter@example.com submitter 2001 'Dummy Submitter' --key-file ${MOZREVIEW_HOME}/keys/submitter@example.com --scm-level 1
  $ exportbzauth submitter@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'Initial Bug'

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Initial commit'
  $ hg --config bugzilla.username=submitter@example.com push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/8c2be86a13c9*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 1 changesets for review
  
  changeset:  1:0aca5e441702
  summary:    Bug 1 - Initial commit
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

Now publish the review and create a new draft

  $ rbmanage publish 1
  $ echo foo3 > foo
  $ hg commit --amend > /dev/null
  $ hg --config bugzilla.username=submitter@example.com push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 1 changesets for review
  
  changeset:  1:b3be3d464d6b
  summary:    Bug 1 - Initial commit
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

We should have a disagreement between published and draft

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: submitter+6
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Initial commit
  - ''
  - 'Pull down this commit:'
  - ''
  - hg pull -r 0aca5e4417025c80407d8f7f22864e8d09fbec50 http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.base_commit: 3a9f6899ef84c99841f546030b036d0124a863cf
    p2rb.commits: '[["0aca5e4417025c80407d8f7f22864e8d09fbec50", 2]]'
    p2rb.discard_on_publish_rids: '[]'
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
    - /r/2 - Bug 1 - Initial commit
    - ''
    - 'Pull down this commit:'
    - ''
    - hg pull -r b3be3d464d6b32130006cbdfa82f9f98a3c57a01 http://*:$HGPORT/test-repo (glob)
    target_people: []
    extra:
      p2rb: true
      p2rb.base_commit: 3a9f6899ef84c99841f546030b036d0124a863cf
      p2rb.commits: '[["b3be3d464d6b32130006cbdfa82f9f98a3c57a01", 2]]'
      p2rb.discard_on_publish_rids: '[]'
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: true
      p2rb.reviewer_map: '{"2": []}'
      p2rb.unpublished_rids: '[]'
    diffs:
    - id: 3
      revision: 2
      base_commit_id: 3a9f6899ef84c99841f546030b036d0124a863cf
      patch:
      - diff --git a/foo b/foo
      - '--- a/foo'
      - +++ b/foo
      - '@@ -1,1 +1,1 @@'
      - -foo
      - +foo3
      - ''

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: submitter+6
  summary: Bug 1 - Initial commit
  description: Bug 1 - Initial commit
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 0aca5e4417025c80407d8f7f22864e8d09fbec50
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  draft:
    bugs:
    - '1'
    commit: null
    summary: Bug 1 - Initial commit
    description: Bug 1 - Initial commit
    target_people: []
    extra:
      p2rb: true
      p2rb.commit_id: b3be3d464d6b32130006cbdfa82f9f98a3c57a01
      p2rb.identifier: bz://1/mynick
      p2rb.is_squashed: false
    diffs:
    - id: 4
      revision: 2
      base_commit_id: 3a9f6899ef84c99841f546030b036d0124a863cf
      patch:
      - diff --git a/foo b/foo
      - '--- a/foo'
      - +++ b/foo
      - '@@ -1,1 +1,1 @@'
      - -foo
      - +foo3
      - ''

Discarding the parent review request draft should discard draft on children

  $ rbmanage discard-review-request-draft 1
  Discarded draft for review request 1

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: submitter+6
  summary: bz://1/mynick
  description:
  - /r/2 - Bug 1 - Initial commit
  - ''
  - 'Pull down this commit:'
  - ''
  - hg pull -r 0aca5e4417025c80407d8f7f22864e8d09fbec50 http://*:$HGPORT/test-repo (glob)
  target_people: []
  extra_data:
    p2rb: true
    p2rb.base_commit: 3a9f6899ef84c99841f546030b036d0124a863cf
    p2rb.commits: '[["0aca5e4417025c80407d8f7f22864e8d09fbec50", 2]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: submitter+6
  summary: Bug 1 - Initial commit
  description: Bug 1 - Initial commit
  target_people: []
  extra_data:
    p2rb: true
    p2rb.commit_id: 0aca5e4417025c80407d8f7f22864e8d09fbec50
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false

Cleanup

  $ mozreview stop
  stopped 8 containers
