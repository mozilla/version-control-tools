#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv rb-test-snarkbot
  $ mozreview create-user snarkbot@example.com password 'Snarkbot :snarkbot' --bugzilla-group editbugs --uid 2000 --scm-level 3 > /dev/null

  $ cat > snarkbot.ini << EOF
  > [pulse]
  > host = ${PULSE_HOST}
  > port = ${PULSE_PORT}
  > userid = guest
  > password = guest
  > exchange = exchange/mozreview/
  > queue = all
  > ssl = False
  > routing_key = #
  > timeout = 60.0
  > [reviewboard]
  > url = ${REVIEWBOARD_URL}
  > user = snarkbot@example.com
  > password = password
  > EOF

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

Create and publish a review for SnarkBot

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ echo foo1 > foo
  $ echo foo1 > foo1
  $ hg add foo1
  $ hg commit -m 'Bug 1 - Foo 1'
  $ echo foo2 > foo
  $ echo foo2 > foo2
  $ hg add foo2
  $ hg commit -m 'Bug 1 - Foo 2'
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 2 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/a4f23bfb8f88-0ce7b28d-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 4 changes to 3 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:729692c35796
  summary:    Bug 1 - Foo 1
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:fb16157e773b
  summary:    Bug 1 - Foo 2
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage publish 1
  $ python -m snarkbot --config-path ../snarkbot.ini
  INFO:mozreviewbot:reviewing commit: 729692c35796 for review request: 2 diff_revision: 1
  INFO:mozreviewbot:looking at file: foo (foo)
  INFO:mozreviewbot:foo1
  
  INFO:mozreviewbot:looking at file: foo1 (foo1)
  INFO:mozreviewbot:foo1
  
  INFO:mozreviewbot:reviewing commit: fb16157e773b for review request: 3 diff_revision: 1
  INFO:mozreviewbot:looking at file: foo (foo)
  INFO:mozreviewbot:foo2
  
  INFO:mozreviewbot:looking at file: foo2 (foo2)
  INFO:mozreviewbot:foo2
  
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
    p2rb: true
    p2rb.commit_id: 729692c35796d9cbd453ccef97ee0d14139c4a09
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 2
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
    - +foo1
    - diff --git a/foo1 b/foo1
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo1
    - '@@ -0,0 +1,1 @@'
    - +foo1
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 1
  reviews:
  - id: 1
    public: true
    ship_it: false
    body_top: 'This is what I think of your changes:'
    body_top_text_type: plain
    diff_comments:
    - id: 1
      public: true
      user: snarkbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 1
      text: seriously?
      text_type: plain
      diff_id: 4
      diff_dest_file: foo
    - id: 2
      public: true
      user: snarkbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 1
      text: seriously?
      text_type: plain
      diff_id: 5
      diff_dest_file: foo1
    diff_count: 2

Cleanup

  $ mozreview stop
  stopped 9 containers
