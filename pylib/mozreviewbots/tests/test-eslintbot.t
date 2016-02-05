#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ . $TESTDIR/pylib/mozreviewbots/tests/helpers.sh
  $ commonenv rb-test-eslintbot

Running setup
  $ eslintsetup

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit' > /dev/null
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null

Create mach
  $ cat >> mach << EOF
  > #!/usr/bin/env python
  > import sys
  > import subprocess
  > subprocess.call(["eslint"] + sys.argv[1:])
  > EOF
  $ chmod +x mach

Create .eslintrc

  $ touch .eslintrc

Create a review request with some busted Javascript in it

  $ bugzilla create-bug TestProduct TestComponent bug1
  $ cat >> test.js << EOF
  > if (foo {
  >   var bar
  > }
  > EOF

  $ hg commit -A -m 'Bug 1 - Some busted Javascript'
  adding .eslintrc
  adding mach
  adding test.js
  $ hg push > /dev/null
  $ rbmanage publish 1

  $ python -m eslintbot --config-path ../eslintbot.ini
  INFO:mozreviewbot:reviewing revision: 719ed7ed9e3e (review request: 2)

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Some busted Javascript
  description:
  - Bug 1 - Some busted Javascript
  - ''
  - 'MozReview-Commit-ID: 124Bxg'
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: 719ed7ed9e3e1a340f443981aa91125b68598369
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
    - diff --git a/.eslintrc b/.eslintrc
    - new file mode 100644
    - diff --git a/mach b/mach
    - new file mode 100755
    - '--- /dev/null'
    - +++ b/mach
    - '@@ -0,0 +1,4 @@'
    - +#!/usr/bin/env python
    - +import sys
    - +import subprocess
    - +subprocess.call(["eslint"] + sys.argv[1:])
    - diff --git a/test.js b/test.js
    - new file mode 100644
    - '--- /dev/null'
    - +++ b/test.js
    - '@@ -0,0 +1,3 @@'
    - +if (foo {
    - +  var bar
    - +}
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 1
  reviews:
  - id: 1
    public: true
    ship_it: false
    body_top:
    - I analyzed your JS changes and found 1 errors.
    - ''
    - 'The following files were examined:'
    - ''
    - '  test.js'
    body_top_text_type: plain
    diff_comments:
    - id: 1
      public: true
      user: eslintbot
      issue_opened: true
      issue_status: open
      first_line: 1
      num_lines: 1
      text: 'Error - Parsing error: Unexpected token { (column 10)'
      text_type: plain
      diff_id: 6
      diff_dest_file: test.js
    diff_count: 1

Cleanup

  $ mozreview stop
  stopped 9 containers
