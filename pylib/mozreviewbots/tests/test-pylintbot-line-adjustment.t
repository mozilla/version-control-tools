#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ . $TESTDIR/pylib/mozreviewbots/tests/helpers.sh
  $ commonenv rb-python-noop
  $ pylintsetup pylintbot.ini

Create tests for line adjustment -= 1

  $ cat >> e121.py << EOF
  > sorted(
  >   [1, 2])
  > EOF

  $ flake8 e121.py
  e121.py:2:3: E121 continuation line under-indented for hanging indent
  [1]

  $ cat >> e122.py << EOF
  > sorted(
  > [1, 2])
  > EOF

  $ flake8 e122.py
  e122.py:2:1: E122 continuation line missing indentation or outdented
  [1]

  $ cat >> e126.py << EOF
  > sorted(
  >         [1, 2])
  > EOF

  $ flake8 e126.py
  e126.py:2:9: E126 continuation line over-indented for hanging indent
  [1]

  $ cat >> e127.py << EOF
  > sorted([1, 2],
  >         cmp=None)
  > EOF

  $ flake8 e127.py
  e127.py:2:9: E127 continuation line over-indented for visual indent
  [1]

  $ cat >> e128.py << EOF
  > sorted([1, 2],
  >     cmp=None)
  > EOF

  $ flake8 e128.py
  e128.py:2:5: E128 continuation line under-indented for visual indent
  [1]

  $ cat >> e131.py << EOF
  > l = [
  >     1,
  >    2]
  > EOF

  $ flake8 e131.py
  e131.py:3:4: E131 continuation line unaligned for hanging indent
  [1]

  $ cat >> e301.py << EOF
  > class Foo(object):
  >     x = None
  >     def foo():
  >         pass
  > EOF

  $ flake8 e301.py
  e301.py:3:5: E301 expected 1 blank line, found 0
  [1]

Line numbers for these failures should be adjusted -= 1 and cover 2 lines

  $ hg -q commit -A -m 'Bug 1 - Line adjustment minus 1'
  $ bugzilla create-bug TestProduct TestComponent bug1

  $ hg push > /dev/null
  $ rbmanage publish 1

  $ python -m pylintbot --config-path ../pylintbot.ini
  INFO:mozreviewbot:reviewing revision: c45aead0c4d6 (review request: 2)

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Line adjustment minus 1
  description:
  - Bug 1 - Line adjustment minus 1
  - ''
  - 'MozReview-Commit-ID: 124Bxg'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.commit_id: c45aead0c4d66a05a22fce427658fba6f3e20f9c
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
    - diff --git a/e121.py b/e121.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e121.py
    - '@@ -0,0 +1,2 @@'
    - +sorted(
    - +  [1, 2])
    - diff --git a/e122.py b/e122.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e122.py
    - '@@ -0,0 +1,2 @@'
    - +sorted(
    - +[1, 2])
    - diff --git a/e126.py b/e126.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e126.py
    - '@@ -0,0 +1,2 @@'
    - +sorted(
    - +        [1, 2])
    - diff --git a/e127.py b/e127.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e127.py
    - '@@ -0,0 +1,2 @@'
    - +sorted([1, 2],
    - +        cmp=None)
    - diff --git a/e128.py b/e128.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e128.py
    - '@@ -0,0 +1,2 @@'
    - +sorted([1, 2],
    - +    cmp=None)
    - diff --git a/e131.py b/e131.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e131.py
    - '@@ -0,0 +1,3 @@'
    - +l = [
    - +    1,
    - +   2]
    - diff --git a/e301.py b/e301.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e301.py
    - '@@ -0,0 +1,4 @@'
    - '+class Foo(object):'
    - +    x = None
    - '+    def foo():'
    - +        pass
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
    - I analyzed your Python changes and found 7 errors.
    - ''
    - 'The following files were examined:'
    - ''
    - '  e121.py'
    - '  e122.py'
    - '  e126.py'
    - '  e127.py'
    - '  e128.py'
    - '  e131.py'
    - '  e301.py'
    body_top_text_type: plain
    diff_comments:
    - id: 1
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 2
      text: 'E121: continuation line under-indented for hanging indent'
      text_type: plain
      diff_id: 8
      diff_dest_file: e121.py
    - id: 2
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 2
      text: 'E122: continuation line missing indentation or outdented'
      text_type: plain
      diff_id: 9
      diff_dest_file: e122.py
    - id: 3
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 2
      text: 'E126: continuation line over-indented for hanging indent'
      text_type: plain
      diff_id: 10
      diff_dest_file: e126.py
    - id: 4
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 2
      text: 'E127: continuation line over-indented for visual indent'
      text_type: plain
      diff_id: 11
      diff_dest_file: e127.py
    - id: 5
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 2
      text: 'E128: continuation line under-indented for visual indent'
      text_type: plain
      diff_id: 12
      diff_dest_file: e128.py
    - id: 6
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 2
      num_lines: 2
      text: 'E131: continuation line unaligned for hanging indent'
      text_type: plain
      diff_id: 13
      diff_dest_file: e131.py
    - id: 7
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 2
      num_lines: 2
      text: 'E301: expected 1 blank line, found 0'
      text_type: plain
      diff_id: 14
      diff_dest_file: e301.py
    diff_count: 7

Create tests for line -= 2

  $ hg -q up -r 0

  $ cat >> e302.py << EOF
  > def foo():
  >     pass
  > 
  > def bar():
  >     pass
  > EOF

  $ flake8 e302.py
  e302.py:4:1: E302 expected 2 blank lines, found 1
  [1]

  $ hg -q commit -A -m 'Bug 2 - Line adjustment minus 2'
  $ bugzilla create-bug TestProduct TestComponent bug2

  $ hg push > /dev/null
  $ rbmanage publish 3
  $ python -m pylintbot --config-path ../pylintbot.ini
  INFO:mozreviewbot:reviewing revision: 51dfa0ded22a (review request: 4)

  $ rbmanage dumpreview 4
  id: 4
  status: pending
  public: true
  bugs:
  - '2'
  commit: null
  submitter: default+5
  summary: Bug 2 - Line adjustment minus 2
  description:
  - Bug 2 - Line adjustment minus 2
  - ''
  - 'MozReview-Commit-ID: 5ijR9k'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.commit_id: 51dfa0ded22aa53d3e7c3d7b5342ba8734c4c6ce
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
    - diff --git a/e302.py b/e302.py
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/e302.py
    - '@@ -0,0 +1,5 @@'
    - '+def foo():'
    - +    pass
    - +
    - '+def bar():'
    - +    pass
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
    - '  e302.py'
    body_top_text_type: plain
    diff_comments:
    - id: 8
      public: true
      user: pylintbot
      issue_opened: true
      issue_status: open
      first_line: 2
      num_lines: 3
      text: 'E302: expected 2 blank lines, found 1'
      text_type: plain
      diff_id: 16
      diff_dest_file: e302.py
    diff_count: 1

Cleanup

  $ mozreview stop
  stopped 9 containers
