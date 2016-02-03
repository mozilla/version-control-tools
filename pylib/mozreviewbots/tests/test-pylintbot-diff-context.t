#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ . $TESTDIR/pylib/mozreviewbots/tests/helpers.sh
  $ commonenv rb-python-noop
  $ pylintsetup pylintbot.ini

Style issues outside of lines changed by the reviewed changeset should
be ignored

  $ cat >> foo.py << EOF
  > import subprocess
  > subprocess.check_call(['program',
  >     'arg'])
  > EOF

  $ flake8 foo.py
  foo.py:3:5: E128 continuation line under-indented for visual indent
  [1]

  $ hg -q commit -A -m 'old file version'
  $ hg phase --public -r .

  $ cat >> foo.py << EOF
  > subprocess.check_call(['program2', 'arg2'])
  > EOF

  $ flake8 foo.py
  foo.py:3:5: E128 continuation line under-indented for visual indent
  [1]

  $ hg commit -m 'Bug 1 - Verify diff context'
  $ bugzilla create-bug TestProduct TestComponent bug1
  $ hg push > /dev/null
  $ rbmanage publish 1

  $ python -m pylintbot --config-path ../pylintbot.ini
  INFO:mozreviewbot:reviewing revision: a89ebf13fcac (review request: 2)

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Verify diff context
  description: Bug 1 - Verify diff context
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb: true
    p2rb.commit_id: a89ebf13fcac33a90fe92db070bc96cb56a0f9db
    p2rb.first_public_ancestor: 3edbb5ae6222fc9890db26538597a9b417cb7b94
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 2
    revision: 1
    base_commit_id: 3edbb5ae6222fc9890db26538597a9b417cb7b94
    name: diff
    extra: {}
    patch:
    - diff --git a/foo.py b/foo.py
    - '--- a/foo.py'
    - +++ b/foo.py
    - '@@ -1,3 +1,4 @@'
    - ' import subprocess'
    - ' subprocess.check_call([''program'','
    - '     ''arg''])'
    - +subprocess.check_call(['program2', 'arg2'])
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"
  review_count: 1
  reviews:
  - id: 1
    public: true
    ship_it: true
    body_top:
    - And now for something completely different.
    - ''
    - Congratulations, there were no Python static analysis issues with this patch!
    - ''
    - 'The following files were examined:'
    - ''
    - '  foo.py'
    body_top_text_type: plain
    diff_comments: []

Cleanup

  $ mozreview stop
  stopped 9 containers
