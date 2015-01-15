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

  $ out=`bugzilla create-login-cookie`
  $ userid=`echo ${out} | awk '{print $1}'`
  $ cookie=`echo ${out} | awk '{print $2}'`

  $ hg --config bugzilla.userid=${userid} --config bugzilla.cookie=${cookie} bzexport --review ':mary'
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

Changing the reviewer works

  $ bugzilla create-bug TestProduct TestComponent bug3
  $ hg qref -m 'Bug 3 - Switching reviewer'
  $ hg bzexport --review :mary
  Requesting review from user1@example.com
  test-reviewer uploaded as http://*:$HGPORT/attachment.cgi?id=3&action=edit (glob)

  $ hg bzexport --review :bob
  Requesting review from user2@example.com
  test-reviewer uploaded as http://*:$HGPORT/attachment.cgi?id=4&action=edit (glob)

  $ bugzilla dump-bug 3
  Bug 3:
    attachments:
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID 863dcf97c40f401dedc9eed21e4579de9c8a4699\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 3 - Switching reviewer\n\ndiff\
        \ -r 96ee1d7354c4 -r 863dcf97c40f foo\n--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n\
        +++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first\n"
      description: Switching reviewer
      file_name: test-reviewer
      flags: []
      id: 3
      is_obsolete: true
      is_patch: true
      summary: Switching reviewer
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID 863dcf97c40f401dedc9eed21e4579de9c8a4699\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 3 - Switching reviewer\n\ndiff\
        \ -r 96ee1d7354c4 -r 863dcf97c40f foo\n--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n\
        +++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first\n"
      description: Switching reviewer
      file_name: test-reviewer
      flags:
      - id: 4
        name: review
        requestee: user2@example.com
        setter: admin@example.com
        status: '?'
      id: 4
      is_obsolete: false
      is_patch: true
      summary: Switching reviewer
    blocks: []
    cc:
    - user1@example.com
    - user2@example.com
    comments:
    - author: admin@example.com
      id: 5
      tags: []
      text: ''
    - author: admin@example.com
      id: 6
      tags: []
      text: 'Created attachment 3
  
        Switching reviewer'
    - author: admin@example.com
      id: 7
      tags: []
      text: 'Created attachment 4
  
        Switching reviewer'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug3

Specifying both reviewer and feedback works

  $ bugzilla create-bug TestProduct TestComponent bug4
  $ hg qref -m 'Bug 4 - Review and feedback'
  $ hg bzexport --review :mary --feedback :bob
  Requesting review from user1@example.com
  Requesting feedback from user2@example.com
  test-reviewer uploaded as http://*:$HGPORT/attachment.cgi?id=5&action=edit (glob)

  $ bugzilla dump-bug 4
  Bug 4:
    attachments:
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID a767676592014b53eb4cdb31cc527db916c265fc\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 4 - Review and feedback\n\n\
        diff -r 96ee1d7354c4 -r a76767659201 foo\n--- a/foo\tThu Jan 01 00:00:00 1970\
        \ +0000\n+++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first\n"
      description: Review and feedback
      file_name: test-reviewer
      flags:
      - id: 5
        name: feedback
        requestee: user2@example.com
        setter: admin@example.com
        status: '?'
      - id: 6
        name: review
        requestee: user1@example.com
        setter: admin@example.com
        status: '?'
      id: 5
      is_obsolete: false
      is_patch: true
      summary: Review and feedback
    blocks: []
    cc:
    - user1@example.com
    - user2@example.com
    comments:
    - author: admin@example.com
      id: 8
      tags: []
      text: ''
    - author: admin@example.com
      id: 9
      tags: []
      text: 'Created attachment 5
  
        Review and feedback'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug4

  $ $TESTDIR/testing/docker-control.py stop-bmo bzexport-test-review
  stopped 2 containers

