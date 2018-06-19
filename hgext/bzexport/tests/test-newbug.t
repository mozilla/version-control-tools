#require bmodocker
  $ $TESTDIR/d0cker start-bmo bzexport-test-newbug $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://$DOCKER_HOSTNAME:$HGPORT/

  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

  $ hg init repo
  $ cd repo

Creating a bug with basic options works

  $ hg newbug --product TestProduct --component TestComponent -t 'First Bug' 'Description'
  Refreshing configuration cache for http://$DOCKER_HOSTNAME:$HGPORT/bzapi/
  Using default version 'unspecified' of product TestProduct
  Created bug 1 at http://$DOCKER_HOSTNAME:$HGPORT/show_bug.cgi?id=1

  $ bugzilla dump-bug 1
  Bug 1:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
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
  Created bug 2 at http://$DOCKER_HOSTNAME:$HGPORT/show_bug.cgi?id=2
  $ bugzilla dump-bug 2
  Bug 2:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
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

  $ adminbugzilla create-user user1@example.com password1 'Mary Jane [:mary]'
  created user 6
  $ adminbugzilla create-user user2@example.com password2 'Bob Jones [:bob]'
  created user 7

  $ hg newbug --cc ':mary,:bob' --product TestProduct --component TestComponent -t 'CC list' 'dummy'
  Using default version 'unspecified' of product TestProduct
  Created bug 3 at http://$DOCKER_HOSTNAME:$HGPORT/show_bug.cgi?id=3

  $ bugzilla dump-bug 3
  Bug 3:
    blocks: []
    cc:
    - user1@example.com
    - user2@example.com
    comments:
    - author: default@example.com
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

Specifying blockers and dependencies works

  $ hg newbug -B 1 -D 2 --product TestProduct --component TestComponent -t 'Dependencies' 'dummy'
  Using default version 'unspecified' of product TestProduct
  Created bug 4 at http://$DOCKER_HOSTNAME:$HGPORT/show_bug.cgi?id=4

  $ bugzilla dump-bug 4
  Bug 4:
    blocks:
    - 1
    cc: []
    comments:
    - author: default@example.com
      id: 4
      tags: []
      text: dummy
    component: TestComponent
    depends_on:
    - 2
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: Dependencies

Cleanup

  $ $TESTDIR/d0cker stop-bmo bzexport-test-newbug
  stopped 2 containers
