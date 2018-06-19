#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug TestProduct TestComponent 'Initial Bug'

  $ cd client
  $ echo foo > foo.h
  $ hg commit -A -m 'root commit'
  adding foo.h
  $ hg phase --public -r .
  $ echo foo1 > foo.h
  $ hg commit -m 'Bug 1 - Foo 1'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/8d901902ff4b-c4c7c89c-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:4a9cf7e91820
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

System is recognizing if a ReviewRequest has been created before implementation
of the commit-message FileDiff feature by fields added to Repository and
CommitData. To make above ReviewRequest look like an old one we need to
remove commit message entries from database.
  $ mozreview sql rbweb <<EOF
  > DELETE FROM diffviewer_filediff WHERE id=2;
  > DELETE FROM diffviewer_diffset WHERE id=2;
  > -- remove has_commit_msg_filediff from parent review_request
  > UPDATE "mozreview_commitdata" SET
  > extra_data='{"p2rb.first_public_ancestor": "df67364c205763de5ad1d2c33fa78f87f6618289", "p2rb.is_squashed": true, "p2rb.base_commit": "df67364c205763de5ad1d2c33fa78f87f6618289", "p2rb.identifier": "bz://1/mynick", "p2rb.discard_on_publish_rids": "[]", "p2rb.unpublished_rids": "[]", "p2rb.commits": "[[\"4a9cf7e9182050f2125ae6c10b21cfc78f6b25ef\", 2]]", "p2rb": true}',
  > draft_extra_data='{"p2rb.first_public_ancestor": "df67364c205763de5ad1d2c33fa78f87f6618289", "p2rb.is_squashed": true, "p2rb.base_commit": "df67364c205763de5ad1d2c33fa78f87f6618289", "p2rb.identifier": "bz://1/mynick", "p2rb.discard_on_publish_rids": "[]", "p2rb.has_temp_diffset": true, "p2rb.unpublished_rids": "[]", "p2rb.commits": "[[\"4a9cf7e9182050f2125ae6c10b21cfc78f6b25ef\", 2]]", "p2rb": true}' WHERE review_request_id=1;
  > -- remove commit_message_filediff_ids and .commit_message_filename
  > UPDATE "mozreview_commitdata" SET
  > extra_data='{"p2rb.first_public_ancestor": "df67364c205763de5ad1d2c33fa78f87f6618289", "p2rb.is_squashed": false, "p2rb.author": "test", "p2rb.identifier": "bz://1/mynick", "p2rb.commit_id": "4a9cf7e9182050f2125ae6c10b21cfc78f6b25ef", "p2rb": true}',
  > draft_extra_data = '{"p2rb.first_public_ancestor": "df67364c205763de5ad1d2c33fa78f87f6618289", "p2rb.is_squashed": false, "p2rb.author": "test", "p2rb.commit_id": "4a9cf7e9182050f2125ae6c10b21cfc78f6b25ef", "p2rb.identifier": "bz://1/mynick", "p2rb": true}'
  > WHERE review_request_id=2;
  > -- remove temp_diffset_id info from repository
  > UPDATE "scmtools_repository" SET extra_data='{}';
  > EOF

  $ reviewboard dumpreview 2
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
    p2rb.commit_id: 4a9cf7e9182050f2125ae6c10b21cfc78f6b25ef
    p2rb.first_public_ancestor: df67364c205763de5ad1d2c33fa78f87f6618289
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 3
    revision: 1
    base_commit_id: df67364c205763de5ad1d2c33fa78f87f6618289
    name: diff
    extra: {}
    patch:
    - diff --git a/foo.h b/foo.h
    - '--- a/foo.h'
    - +++ b/foo.h
    - '@@ -1,1 +1,1 @@'
    - -foo
    - +foo1
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Ammending commit should not create a commit message FileDiff
  $ echo foo2 > foo.h
  $ hg commit --amend -m 'Bug 1 - Foo 2'
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/4a9cf7e91820-*.hg (glob)
  $ hg push -y
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/ecf3ba3ae44d-df5ba11c-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:1677aa2f30f2
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

  $ reviewboard dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 2
  description:
  - Bug 1 - Foo 2
  - ''
  - 'MozReview-Commit-ID: 5ijR9k'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test
    p2rb.commit_id: 1677aa2f30f2071c46bd008be11b401675803676
    p2rb.first_public_ancestor: df67364c205763de5ad1d2c33fa78f87f6618289
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 3
    revision: 1
    base_commit_id: df67364c205763de5ad1d2c33fa78f87f6618289
    name: diff
    extra: {}
    patch:
    - diff --git a/foo.h b/foo.h
    - '--- a/foo.h'
    - +++ b/foo.h
    - '@@ -1,1 +1,1 @@'
    - -foo
    - +foo1
    - ''
  - id: 5
    revision: 2
    base_commit_id: df67364c205763de5ad1d2c33fa78f87f6618289
    name: diff
    extra: {}
    patch:
    - diff --git a/foo.h b/foo.h
    - '--- a/foo.h'
    - +++ b/foo.h
    - '@@ -1,1 +1,1 @@'
    - -foo
    - +foo2
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Entirely new review request within the same parent also has no commit message
FileDiff.
  $ echo bar > bar.txt
  $ hg commit -A -m 'Bug 1 - Bar'
  adding bar.txt
  $ hg push -y
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/70dc6201428b-74f41091-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:1677aa2f30f2
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  2:dc2971575b0d
  summary:    Bug 1 - Bar
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

  $ reviewboard dumpreview 3
  id: 3
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Bar
  description:
  - Bug 1 - Bar
  - ''
  - 'MozReview-Commit-ID: APOgLo'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test
    p2rb.commit_id: dc2971575b0de9214b29406e986ff8a666f7d396
    p2rb.first_public_ancestor: df67364c205763de5ad1d2c33fa78f87f6618289
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 7
    revision: 1
    base_commit_id: 1677aa2f30f2071c46bd008be11b401675803676
    name: diff
    extra: {}
    patch:
    - diff --git a/bar.txt b/bar.txt
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/bar.txt
    - '@@ -0,0 +1,1 @@'
    - +bar
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Cleanup

  $ mozreview stop
  stopped 7 containers
