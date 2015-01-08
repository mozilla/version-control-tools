#require docker
  $ $TESTDIR/testing/docker-control.py start-bmo bzexport-test-newbug $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://*:$HGPORT/ (glob)

  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

  $ hg init repo
  $ cd repo
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

Cleanup

  $ $TESTDIR/testing/docker-control.py stop-bmo bzexport-test-newbug
  stopped 2 containers
