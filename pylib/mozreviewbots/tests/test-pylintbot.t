#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ . $TESTDIR/pylib/mozreviewbots/tests/helpers.sh
  $ commonenv rb-python-noop
  $ pylintsetup pylintbot.ini

Create a review with Python style violations

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ cat >> foo.py << EOF
  > def a(): pass
  > 
  >   
  > def b():
  >     foo = True
  > EOF

  $ hg -q commit -A -m 'Bug 1 - Bad Python'
  $ hg push > /dev/null
  $ rbmanage publish 1
  $ python -m pylintbot --config-path ../pylintbot.ini
  INFO:mozreviewbot:reviewing revision: 1978e5417012 (review request: 2)

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Bad Python
  description:
  - Bug 1 - Bad Python
  - ''
  - 'MozReview-Commit-ID: 124Bxg'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.commit_id: 1978e5417012a5f63128d09cfd52c52077c761cb
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
    - diff --git a/foo.py b/foo.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/foo.py
    - '@@ -0,0 +1,5 @@'
    - '+def a(): pass'
    - +
    - '+  '
    - '+def b():'
    - +    foo = True
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 1
  reviews:
  - id: 1
    public: true
    ship_it: false
    body_top:
    - Always look on the bright side of life.
    - ''
    - I analyzed your Python changes and found 3 errors.
    - ''
    - 'The following files were examined:'
    - ''
    - '  foo.py'
    body_top_text_type: plain
    diff_comments:
    - id: 1
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 1
      text: 'E701: multiple statements on one line (colon)'
      text_type: plain
      diff_id: 2
      diff_dest_file: foo.py
    - id: 2
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 3
      num_lines: 1
      text: 'W293: blank line contains whitespace'
      text_type: plain
      diff_id: 2
      diff_dest_file: foo.py
    - id: 3
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 5
      num_lines: 1
      text: 'F841: local variable ''foo'' is assigned to but never used'
      text_type: plain
      diff_id: 2
      diff_dest_file: foo.py
    diff_count: 3

Ensure pyflakes warnings are handled

  $ hg -q up -r 0
  $ cat >> f401.py << EOF
  > import sys
  > EOF

  $ hg -q commit -A -m 'Bug 2 - pyflakes'
  $ bugzilla create-bug TestProduct TestComponent bug1
  $ hg push > /dev/null

  $ rbmanage publish 3

  $ python -m pylintbot --config-path ../pylintbot.ini
  INFO:mozreviewbot:reviewing revision: c768227fc261 (review request: 4)

  $ rbmanage dumpreview 4
  id: 4
  status: pending
  public: true
  bugs:
  - '2'
  commit: null
  submitter: default+5
  summary: Bug 2 - pyflakes
  description:
  - Bug 2 - pyflakes
  - ''
  - 'MozReview-Commit-ID: 5ijR9k'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.commit_id: c768227fc261de5a93e0c813e0ba4a54e24d2697
    p2rb.first_public_ancestor: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    p2rb.identifier: bz://2/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 4
    revision: 1
    base_commit_id: 7c5bdf0cec4a90edb36300f8f3679857f46db829
    name: diff
    extra: {}
    patch:
    - diff --git a/f401.py b/f401.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/f401.py
    - '@@ -0,0 +1,1 @@'
    - +import sys
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 1
  reviews:
  - id: 2
    public: true
    ship_it: false
    body_top:
    - Always look on the bright side of life.
    - ''
    - I analyzed your Python changes and found 1 errors.
    - ''
    - 'The following files were examined:'
    - ''
    - '  f401.py'
    body_top_text_type: plain
    diff_comments:
    - id: 4
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 1
      text: 'F401: ''sys'' imported but unused'
      text_type: plain
      diff_id: 4
      diff_dest_file: f401.py
    diff_count: 1

Cleanup

  $ mozreview stop
  stopped 9 containers
