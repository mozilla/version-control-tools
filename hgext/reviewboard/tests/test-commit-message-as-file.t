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

Commit extra data fields should be created

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
    p2rb.commit_message_filediff_ids: '{"1": 2}'
    p2rb.commit_message_filename: commit-message-df673
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

Amended commit message should result with a changed commit message ids extra 
data, filename should remain the same.

  $ hg commit --amend -m 'Bug 1 - Foo 2 - amended'
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/4a9cf7e91820-f76b5126-*.hg (glob)
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/2358ed0ad9b5-42479a45-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:b649587d0bcc
  summary:    Bug 1 - Foo 2 - amended
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
  summary: Bug 1 - Foo 2 - amended
  description:
  - Bug 1 - Foo 2 - amended
  - ''
  - 'MozReview-Commit-ID: 5ijR9k'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test
    p2rb.commit_id: b649587d0bcc3c194fe76d91bf1329a1f7590e28
    p2rb.commit_message_filediff_ids: '{"1": 2, "2": 5}'
    p2rb.commit_message_filename: commit-message-df673
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
    - +foo1
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Cleanup

  $ mozreview stop
  stopped 9 containers
