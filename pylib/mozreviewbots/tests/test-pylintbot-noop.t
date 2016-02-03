#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ . $TESTDIR/pylib/mozreviewbots/tests/helpers.sh
  $ commonenv rb-python-noop
  $ pylintsetup pylintbot.ini

Create a review request that doesn't touch any Python files

  $ bugzilla create-bug TestProduct TestComponent bug1
  $ echo irrelevant > foo
  $ hg commit -m 'Bug 1 - No Python changes'
  $ hg push > /dev/null
  $ rbmanage publish 1

No review should be left if no Python files were changed.

  $ python -m pylintbot --config-path ../pylintbot.ini
  INFO:mozreviewbot:reviewing revision: 9408145328c3 (review request: 2)
  INFO:mozreviewbot:not reviewing revision: 9408145328c39ed1fe384e35788b069524ca71a6 no relevant python changes in commit

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - No Python changes
  description: Bug 1 - No Python changes
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: 9408145328c39ed1fe384e35788b069524ca71a6
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
    - +irrelevant
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

If only changes are deletions, then no review should be posted

  $ bugzilla create-bug TestProduct TestComponent bug2
  $ hg -q up -r 0
  $ echo dummy > test.py
  $ hg -q commit -A -m 'Add test.py'
  $ hg phase --public -r .
  $ hg rm test.py
  $ hg commit -m 'Bug 2 - Delete test.py'

  $ hg push > /dev/null
  $ rbmanage publish 3

  $ python -m pylintbot --config-path ../pylintbot.ini
  INFO:mozreviewbot:reviewing revision: dddca45a4bed (review request: 4)
  INFO:mozreviewbot:not reviewing revision: dddca45a4bedd629833af826c138bd7e302e5807 no relevant python changes in commit

Expecting 0 reviews

  $ rbmanage dumpreview 3
  id: 3
  status: pending
  public: true
  bugs:
  - '2'
  commit: bz://2/mynick
  submitter: default+5
  summary: bz://2/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.base_commit: f5e6079765d8be2554c86ef044e269f048871f1d
    p2rb.commits: '[["dddca45a4bedd629833af826c138bd7e302e5807", 4]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.first_public_ancestor: f5e6079765d8be2554c86ef044e269f048871f1d
    p2rb.identifier: bz://2/mynick
    p2rb.is_squashed: true
    p2rb.reviewer_map: '{}'
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 3
    revision: 1
    base_commit_id: f5e6079765d8be2554c86ef044e269f048871f1d
    name: diff
    extra: {}
    patch:
    - diff --git a/test.py b/test.py
    - deleted file mode 100644
    - '--- a/test.py'
    - +++ /dev/null
    - '@@ -1,1 +0,0 @@'
    - -dummy
    - ''
  approved: false
  approval_failure: Commit dddca45a4bedd629833af826c138bd7e302e5807 is not approved.

Cleanup

  $ mozreview stop
  stopped 9 containers
