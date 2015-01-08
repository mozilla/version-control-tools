#require docker
  $ $TESTDIR/testing/docker-control.py start-bmo bzexport-test-newbug $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://*:$HGPORT/ (glob)

  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

  $ hg init repo
  $ cd repo

Creating a bug with basic options works

  $ hg newbug --product TestProduct --component TestComponent -t 'First Bug' 'Description'
  Refreshing configuration cache for http://*:$HGPORT/bzapi/ (glob)
  Using default version 'unspecified' of product TestProduct
  Created bug 1 at http://*:$HGPORT/show_bug.cgi?id=1 (glob)

  $ bugzilla dump-bug 1
  Bug 1:
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 1
      tags: []
      text: Description
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: First Bug

Assigning a bug works

  $ hg newbug --take-bug --product TestProduct --component TestComponent -t 'Assign it' 'dummy'
  Using default version 'unspecified' of product TestProduct
  Created bug 2 at http://*:$HGPORT/show_bug.cgi?id=2 (glob)
  $ bugzilla dump-bug 2
  Bug 2:
    blocks: []
    cc: []
    comments:
    - author: admin@example.com
      id: 2
      tags: []
      text: dummy
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: ASSIGNED
    summary: Assign it

Specifying a CC list works

  $ bugzilla create-user user1@example.com password1 'Mary Jane [:mary]'
  created user 5
  $ bugzilla create-user user2@example.com password2 'Bob Jones [:bob]'
  created user 6

  $ hg newbug --cc ':mary,:bob' --product TestProduct --component TestComponent -t 'CC list' 'dummy'
  Using default version 'unspecified' of product TestProduct
  Created bug 3 at http://192.168.59.103:$HGPORT/show_bug.cgi?id=3

  $ bugzilla dump-bug 3
  Bug 3:
    blocks: []
    cc:
    - user1@example.com
    - user2@example.com
    comments:
    - author: admin@example.com
      id: 3
      tags: []
      text: dummy
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: CC list

Cleanup

  $ $TESTDIR/testing/docker-control.py stop-bmo bzexport-test-newbug
  stopped 2 containers
