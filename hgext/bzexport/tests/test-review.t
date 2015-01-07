#require docker
  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

  $ $TESTDIR/testing/docker-control.py start-bmo bzexport-test-review $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://*:$HGPORT/ (glob)

Create some Bugzilla users

  $ bugzilla create-user user1@example.com password1 'Mary Jane [:mary]'
  created user 5
  $ bugzilla create-user user2@example.com password2 'Bob Jones [:bob]'
  created user 6

Set up repo and Bugzilla state

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg -q commit -A -m 'initial'

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug1

Specifying a reviewer by IRC nick works

  $ echo first > foo
  $ hg qnew -d '0 0' -m 'Bug 1 - Testing reviewer' test-reviewer
  $ hg bzexport --review ':mary'
  Refreshing configuration cache for http://*:$HGPORT/bzapi/ (glob)
  Requesting review from user1@example.com
  test-reviewer uploaded as http://*:$HGPORT/attachment.cgi?id=1&action=edit (glob)

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID 141273a2a25953ea9b916eb5d232728c6ef01383\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 1 - Testing reviewer\n\ndiff\
        \ -r 96ee1d7354c4 -r 141273a2a259 foo\n--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n\
        +++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first\n"
      description: Testing reviewer
      file_name: test-reviewer
      flags:
      - id: 1
        name: review
        requestee: user1@example.com
        setter: admin@example.com
        status: '?'
      id: 1
      is_obsolete: false
      is_patch: true
      summary: Testing reviewer
    blocks: []
    cc:
    - user1@example.com
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: ''
    - author: admin@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        Testing reviewer'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

Parsing reviewer out of commit message works

  $ bugzilla create-bug TestProduct TestComponent bug2
  $ hg qref -m 'Bug 2 - Auto reviewer; r=bob'
  $ hg bzexport --review auto
  Requesting review from user2@example.com
  test-reviewer uploaded as http://*:$HGPORT/attachment.cgi?id=2&action=edit (glob)

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID 69fb1288e32b83586e070b678ead805e6a48fba7\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 2 - Auto reviewer; r=bob\n\n\
        diff -r 96ee1d7354c4 -r 69fb1288e32b foo\n--- a/foo\tThu Jan 01 00:00:00 1970\
        \ +0000\n+++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first\n"
      description: Auto reviewer
      file_name: test-reviewer
      flags:
      - id: 2
        name: review
        requestee: user2@example.com
        setter: admin@example.com
        status: '?'
      id: 2
      is_obsolete: false
      is_patch: true
      summary: Auto reviewer
    blocks: []
    cc:
    - user2@example.com
    comments:
    - author: admin@example.com
      id: 3
      tags: []
      text: ''
    - author: admin@example.com
      id: 4
      tags: []
      text: 'Created attachment 2
  
        Auto reviewer'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug2

  $ $TESTDIR/testing/docker-control.py stop-bmo bzexport-test-review
  stopped 2 containers

