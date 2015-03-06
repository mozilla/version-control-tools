#require docker
  $ $TESTDIR/testing/docker-control.py start-bmo bzexport-test-patch-create $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://*:$HGPORT/ (glob)

  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg -q commit -A -m 'initial'

Uploading a simple patch to a bug works

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ echo first > foo
  $ hg qnew -d '0 0' -m 'Bug 1 - First patch' first-patch
  $ hg bzexport
  Refreshing configuration cache for http://*:$HGPORT/bzapi/ (glob)
  first-patch uploaded as http://*:$HGPORT/attachment.cgi?id=1&action=edit (glob)

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID ac5453011ddd13f327fa0ffb7d7e91fc51d86f39\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 1 - First patch\n\ndiff -r 96ee1d7354c4\
        \ -r ac5453011ddd foo\n--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n+++ b/foo\t\
        Thu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first\n"
      description: First patch
      file_name: first-patch
      flags: []
      id: 1
      is_obsolete: false
      is_patch: true
      summary: First patch
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: ''
    - author: admin@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        First patch'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

Updating the patch works

  $ echo first2 > foo
  $ hg qref -m 'Bug 1 - First patch again'
  $ hg bzexport
  first-patch uploaded as http://*:$HGPORT/attachment.cgi?id=2&action=edit (glob)

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID ac5453011ddd13f327fa0ffb7d7e91fc51d86f39\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 1 - First patch\n\ndiff -r 96ee1d7354c4\
        \ -r ac5453011ddd foo\n--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n+++ b/foo\t\
        Thu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first\n"
      description: First patch
      file_name: first-patch
      flags: []
      id: 1
      is_obsolete: true
      is_patch: true
      summary: First patch
    - attacher: admin@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID 126f93d96a111d3a795db22137198ddb95995d23\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 1 - First patch again\n\ndiff\
        \ -r 96ee1d7354c4 -r 126f93d96a11 foo\n--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n\
        +++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+first2\n"
      description: First patch again
      file_name: first-patch
      flags: []
      id: 2
      is_obsolete: false
      is_patch: true
      summary: First patch again
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: ''
    - author: admin@example.com
      id: 2
      tags: []
      text: 'Created attachment 1
  
        First patch'
    - author: admin@example.com
      id: 3
      tags: []
      text: 'Created attachment 2
  
        First patch again'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

  $ hg -q qpop -a
  patch queue now empty

Uploading a new patch will reassign bug to you

  $ adminbugzilla create-user original-author@example.com password1 'Original Author' --group editbugs
  created user 5

  $ bugzilla create-bug TestProduct TestComponent bug2
  $ echo initial-author > foo
  $ hg qnew -d '0 0' -m 'Bug 2 - Initial author' some-patch
  $ hg --config bugzilla.username=original-author@example.com --config bugzilla.password=password1 bzexport
  some-patch uploaded as http://*:$HGPORT/attachment.cgi?id=3&action=edit (glob)

  $ bugzilla dump-bug 2
  Bug 2:
    attachments:
    - attacher: original-author@example.com
      content_type: text/plain
      data: "# HG changeset patch\n# User test\n# Date 0 0\n#      Thu Jan 01 00:00:00\
        \ 1970 +0000\n# Node ID cecfd177524092b38595878e4a3ffe5b0c74e85b\n# Parent \
        \ 96ee1d7354c4ad7372047672c36a1f561e3a6a4c\nBug 2 - Initial author\n\ndiff -r\
        \ 96ee1d7354c4 -r cecfd1775240 foo\n--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n\
        +++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n@@ -0,0 +1,1 @@\n+initial-author\n"
      description: Initial author
      file_name: some-patch
      flags: []
      id: 3
      is_obsolete: false
      is_patch: true
      summary: Initial author
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 4
      tags: []
      text: ''
    - author: original-author@example.com
      id: 5
      tags: []
      text: 'Created attachment 3
  
        Initial author'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: ASSIGNED
    summary: bug2

  $ $TESTDIR/testing/docker-control.py stop-bmo bzexport-test-patch-create
  stopped 2 containers
