#require docker
  $ $TESTDIR/d0cker start-bmo bzpost-test-post $HGPORT1
  waiting for Bugzilla to start
  Bugzilla accessible on http://*:$HGPORT1/ (glob)

  $ export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT1
  $ $TESTDIR/bugzilla create-user default@example.com password 'Default User' --group editbugs
  created user 5

  $ export BUGZILLA_USERNAME=default@example.com
  $ export BUGZILLA_PASSWORD=password

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bzpost = $TESTDIR/hgext/bzpost
  > bzauth = $TESTDIR/pylib/mozhg/mozhg/tests/auth.py
  > localmozrepo = $TESTDIR/testing/local-mozilla-repos.py
  > strip =
  > 
  > [localmozrepo]
  > readuri = http://localhost:$HGPORT/
  > writeuri = http://localhost:$HGPORT/
  > 
  > [bugzilla]
  > username = default@example.com
  > password = password
  > url = ${BUGZILLA_URL}/rest
  > 
  > [bzpost]
  > debugcomments = True
  > EOF

  $ hg init mozilla-central
  $ cd mozilla-central
  $ cat >> .hg/hgrc << EOF
  > [web]
  > push_ssl = False
  > allow_push = *
  > EOF

  $ echo initial > foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg phase --public -r .
  $ cd ..

  $ mkdir integration
  $ hg clone mozilla-central integration/mozilla-inbound > /dev/null
  $ cp mozilla-central/.hg/hgrc integration/mozilla-inbound/.hg/hgrc

  $ hg clone mozilla-central try > /dev/null
  $ cp mozilla-central/.hg/hgrc try/.hg/hgrc
  $ cd try
  $ cat >> .hg/hgrc << EOF
  > [phases]
  > publish = False
  > EOF
  $ cd ..

  $ mkdir -p users/bzpost_mozilla.com
  $ hg clone mozilla-central users/bzpost_mozilla.com/mozilla-central > /dev/null
  $ cp try/.hg/hgrc users/bzpost_mozilla.com/mozilla-central/.hg/hgrc

  $ cat >> hgweb << EOF
  > [paths]
  > / = *
  > EOF
  $ hg serve -d -p $HGPORT --pid-file hg.pid --web-conf hgweb
  $ cat hg.pid >> $DAEMON_PIDS

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug1

Pushing to mozilla-inbound will result in bug being updated

  $ hg clone mozilla-central mi-push > /dev/null
  $ cd mi-push
  $ echo mc > foo
  $ hg commit -m 'Bug 1 - Commit to inbound'
  $ hg push http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  recording push at http://*:$HGPORT1/show_bug.cgi?id=1 (glob)

  $ $TESTDIR/bugzilla dump-bug 1
  Bug 1:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 2
      tags: []
      text:
      - 'url:        http://localhost:$HGPORT/integration/mozilla-inbound/rev/b507e8e331609b343b4f2207cb9f899ff00aef0c'
      - 'changeset:  b507e8e331609b343b4f2207cb9f899ff00aef0c'
      - 'user:       test'
      - 'date:       Thu Jan 01 00:00:00 1970 +0000'
      - 'description:'
      - Bug 1 - Commit to inbound
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

Pushing multiple changesets with multiple bugs will result in bug being updated

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug2
  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug3

  $ echo 2_1 > foo
  $ cat > message << EOF
  > Bug 2 - First commit
  > 
  > This is a long commit message.
  > 
  > With multiple lines in the commit message. This is a long paragraph.
  > It will test wrapping.
  > EOF
  $ hg commit -l message
  $ echo 2_2 > foo
  $ cat > message << EOF
  > Bug 2 - Second commit
  > 
  > This is a commit.
  > EOF
  $ hg commit -l message
  $ rm -f message
  $ echo 3_1 > foo
  $ hg commit -m 'Bug 3 - Another bug'
  $ hg push http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files
  recording push at http://*:$HGPORT1/show_bug.cgi?id=2 (glob)
  recording push at http://*:$HGPORT1/show_bug.cgi?id=3 (glob)

  $ $TESTDIR/bugzilla dump-bug 2 3
  Bug 2:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 3
      tags: []
      text: ''
    - author: default@example.com
      id: 5
      tags: []
      text:
      - 'url:        http://localhost:$HGPORT/integration/mozilla-inbound/rev/7edeca8d7f49bf5bc3c979fdc4b094c7854381c3'
      - 'changeset:  7edeca8d7f49bf5bc3c979fdc4b094c7854381c3'
      - 'user:       test'
      - 'date:       Thu Jan 01 00:00:00 1970 +0000'
      - 'description:'
      - Bug 2 - First commit
      - ''
      - This is a long commit message.
      - ''
      - With multiple lines in the commit message. This is a long paragraph.
      - It will test wrapping.
      - ''
      - 'url:        http://localhost:$HGPORT/integration/mozilla-inbound/rev/d9ef0680b2c01b81a6b1057fb368d4c9ea54d7db'
      - 'changeset:  d9ef0680b2c01b81a6b1057fb368d4c9ea54d7db'
      - 'user:       test'
      - 'date:       Thu Jan 01 00:00:00 1970 +0000'
      - 'description:'
      - Bug 2 - Second commit
      - ''
      - This is a commit.
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug2
  Bug 3:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 4
      tags: []
      text: ''
    - author: default@example.com
      id: 6
      tags: []
      text:
      - 'url:        http://localhost:$HGPORT/integration/mozilla-inbound/rev/d2c84e3fb8c79f9699d4eb6537b155e09e290ec4'
      - 'changeset:  d2c84e3fb8c79f9699d4eb6537b155e09e290ec4'
      - 'user:       test'
      - 'date:       Thu Jan 01 00:00:00 1970 +0000'
      - 'description:'
      - Bug 3 - Another bug
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug3

  $ cd ..

Pushing to Try will post Treeherder comment

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug4

  $ hg clone -r 0 try client > /dev/null
  $ cd client
  $ echo expected > foo
  $ hg commit -m 'Bug 4 - Add foo'
  $ echo foo > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  recording Treeherder push at http://*:$HGPORT1/show_bug.cgi?id=4 (glob)

  $ $TESTDIR/bugzilla dump-bug 4
  Bug 4:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 7
      tags: []
      text: ''
    - author: default@example.com
      id: 8
      tags: []
      text: https://treeherder.mozilla.org/#/jobs?repo=try&revision=311111800824
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug4

  $ cd ..

Public changesets pushed to Try will be ignored if no bug in draft changesets

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug5
  $ hg clone -r 0 try no-bug-in-draft > /dev/null
  $ cd no-bug-in-draft
  $ echo no-bug-in-draft > foo
  $ hg commit -m 'Bug 5 - This should be irrelevant'
  $ hg phase --public -r .
  $ echo foo > foo
  $ hg commit -m 'New draft changeset without bug'
  $ echo try > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push --force http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files (+1 heads)

  $ $TESTDIR/bugzilla dump-bug 5
  Bug 5:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 9
      tags: []
      text: ''
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug5

  $ cd ..

Public changesets pushed to Try will be ignored if a bug in draft changesets

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug6

  $ hg clone -r 0 try bug-in-draft > /dev/null
  $ cd bug-in-draft
  $ echo bug-in-draft > foo
  $ hg commit -m 'Bug 5 - This should also irrelevant'
  $ hg phase --public -r .
  $ echo foo > foo
  $ hg commit -m 'Bug 6 - New draft changeset with bug'
  $ echo try > foo
  $ hg commit -m 'try: -b do -p all -u all -t all'
  $ hg push --force http://localhost:$HGPORT/try
  pushing to http://localhost:$HGPORT/try
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 1 files (+1 heads)
  recording Treeherder push at http://*:$HGPORT1/show_bug.cgi?id=6 (glob)

  $ $TESTDIR/bugzilla dump-bug 5 6
  Bug 5:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 9
      tags: []
      text: ''
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug5
  Bug 6:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 10
      tags: []
      text: ''
    - author: default@example.com
      id: 11
      tags: []
      text: https://treeherder.mozilla.org/#/jobs?repo=try&revision=9257b757fa7a
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug6

  $ cd ..

Pushing commit with bug number to user repo will not post comment by default

  $ hg clone -r 0 users/bzpost_mozilla.com/mozilla-central no-post-to-user > /dev/null
  $ cd no-post-to-user
  $ echo 'no post to user repo' > foo
  $ hg commit -m 'Bug 123 - New changeset with bug.'
  $ hg push http://localhost:$HGPORT/users/bzpost_mozilla.com/mozilla-central
  pushing to http://localhost:$HGPORT/users/bzpost_mozilla.com/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  $ cd ..

Pushing commit with bug number to user repo will post comment if enabled

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug7
  $ hg clone users/bzpost_mozilla.com/mozilla-central post-to-user > /dev/null
  $ cd post-to-user
  $ cat >> .hg/hgrc << EOF
  > [bzpost]
  > updateuserrepo = True
  > EOF

  $ echo 'post to user repo' > foo
  $ hg commit -m 'Bug 7 - New changeset with bug.'
  $ hg push http://localhost:$HGPORT/users/bzpost_mozilla.com/mozilla-central
  pushing to http://localhost:$HGPORT/users/bzpost_mozilla.com/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  recording push at http://*:$HGPORT1/show_bug.cgi?id=7 (glob)

  $ $TESTDIR/bugzilla dump-bug 7
  Bug 7:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 12
      tags: []
      text: ''
    - author: default@example.com
      id: 13
      tags: []
      text:
      - 'url:        http://localhost:$HGPORT/users/bzpost_mozilla.com/mozilla-central/rev/e48ee73711db53ffbde012f289787998e918ccba'
      - 'changeset:  e48ee73711db53ffbde012f289787998e918ccba'
      - 'user:       test'
      - 'date:       Thu Jan 01 00:00:00 1970 +0000'
      - 'description:'
      - Bug 7 - New changeset with bug.
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug7

  $ cd ..

Verify cookie auth works

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug8
  $ mkdir profiles
  $ export FIREFOX_PROFILES_DIR=`pwd`/profiles
  $ cat > profiles/profiles.ini << EOF
  > [Profile0]
  > Name=foo
  > IsRelative=1
  > Path=foo
  > EOF

  $ mkdir profiles/foo
  $ BUGZILLA_USERNAME=default@example.com BUGZILLA_PASSWORD=password out=`$TESTDIR/bugzilla create-login-cookie`
  $ userid=`echo ${out} | awk '{print $1}'`
  $ cookie=`echo ${out} | awk '{print $2}'`
  $ hg bzcreatecookie profiles/foo ${BUGZILLA_URL} ${userid} ${cookie}

  $ hg -q clone http://localhost:$HGPORT/integration/mozilla-inbound cookie-auth
  $ cd cookie-auth
  $ echo cookie > foo
  $ hg commit -m 'Bug 8 - Test cookie auth'
  $ hg --config bugzilla.username= --config bugzilla.password= push
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  recording push at http://*:$HGPORT1/show_bug.cgi?id=8 (glob)

  $ $TESTDIR/bugzilla dump-bug 8
  Bug 8:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 14
      tags: []
      text: ''
    - author: default@example.com
      id: 15
      tags: []
      text:
      - 'url:        http://localhost:$HGPORT/integration/mozilla-inbound/rev/61dd85eacc29239f31fe4791555a17a8e4590904'
      - 'changeset:  61dd85eacc29239f31fe4791555a17a8e4590904'
      - 'user:       test'
      - 'date:       Thu Jan 01 00:00:00 1970 +0000'
      - 'description:'
      - Bug 8 - Test cookie auth
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug8

  $ unset FIREFOX_PROFILES_DIR

  $ cd ..

Pushing commit with bug number to excluded tree will not post comment

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug9
  $ hg clone -r 0 mozilla-central no-post-to-excludetrees > /dev/null
  $ cd no-post-to-excludetrees
  $ cat >> .hg/hgrc << EOF
  > [bzpost]
  > excludetrees = inbound
  > EOF

  $ echo 'no post to excludetrees' > foo
  $ hg commit -m 'Bug 9 - New changeset with bug.'
  $ hg push -f http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)

  $ $TESTDIR/bugzilla dump-bug 9
  Bug 9:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 16
      tags: []
      text: ''
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug9

  $ cd ..

Unicode in author and commit message works

  $ $TESTDIR/bugzilla create-bug TestProduct TestComponent bug10
  $ hg -q clone -r 0 mozilla-central unicode
  $ cd unicode

  $ echo unicode > foo
  $ cat > message << EOF
  > Bug 10 - I am Quèze!
  > EOF
  $ HGENCODING=utf-8 HGUSER='Quèze' hg commit -l message

  $ hg push -f http://localhost:$HGPORT/integration/mozilla-inbound
  pushing to http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  recording push at http://*:$HGPORT1/show_bug.cgi?id=10 (glob)

  $ $TESTDIR/bugzilla dump-bug 10
  Bug 10:
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 17
      tags: []
      text: ''
    - author: default@example.com
      id: 18
      tags: []
      text:
      - 'url:        http://localhost:$HGPORT/integration/mozilla-inbound/rev/853e7b5582a855a0657750740aef6eee540187bb'
      - 'changeset:  853e7b5582a855a0657750740aef6eee540187bb'
      - "user:       Qu\xE8ze"
      - 'date:       Thu Jan 01 00:00:00 1970 +0000'
      - 'description:'
      - "Bug 10 - I am Qu\xE8ze!"
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug10

  $ cd ..

Cleanup

  $ $TESTDIR/d0cker stop-bmo bzpost-test-post
  stopped 2 containers
