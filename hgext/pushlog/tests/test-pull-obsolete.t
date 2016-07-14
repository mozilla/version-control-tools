  $ . $TESTDIR/hghooks/tests/common.sh

  $ cat >> $HGRCPATH << EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > [experimental]
  > evolution = all
  > [extensions]
  > rebase =
  > EOF

  $ export USER=hguser
  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > [phases]
  > publish = false
  > EOF
  $ cd ..

  $ hg -q clone ssh://user@dummy/$TESTTMP/server client
  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ touch file0
  $ hg -q commit -A -m file0
  $ hg -q push
  $ hg -q up -r 0
  $ touch file1
  $ hg -q commit -A -m file1
  $ hg -q push -f
  $ hg rebase -s . -d 1
  rebasing 2:80c2c663cb83 "file1" (tip)
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files
  remote: recorded push in pushlog
  remote: 1 new obsolescence markers

  $ hg --hidden log -G
  @  changeset:   3:a129f82339bb
  |  tag:         tip
  |  parent:      1:ae13d9da6966
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     file1
  |
  | x  changeset:   2:80c2c663cb83
  | |  parent:      0:96ee1d7354c4
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     file1
  | |
  o |  changeset:   1:ae13d9da6966
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     file0
  |
  o  changeset:   0:96ee1d7354c4
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

  $ cd ..

Server pushlog should have 4 pushes and push from hidden changeset (80c2c663cb83)

  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: ae13d9da6966307c98b60987fb4fedc2e2f29736 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 2; Node: 80c2c663cb8364f6898662a8379cb25df3ebe719 (re)
  ID: 4; user: hguser; Date: \d+; Rev: 3; Node: a129f82339bb933c4d72353c44bb29eb685f3d1e (re)

Cloning normally will receive obsolete data

  $ hg clone -U ssh://user@dummy/$TESTTMP/server clone-obsolete1
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 3 files
  1 new obsolescence markers

Default behavior of pushlog is to stop applying incoming push data when it sees
an unknown changeset. Since hidden changesets aren't transferred normally,
pushlog will stop replicating when it encounters a hidden changeset.

  $ hg -R clone-obsolete1 --config extensions.pushlog=$TESTDIR/hgext/pushlog pull
  pulling from ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  received pushlog entry for unknown changeset; ignoring
  added 2 pushes

Pushlog stops at 80c2c663cb83 because it is hidden

  $ dumppushlog clone-obsolete1
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: ae13d9da6966307c98b60987fb4fedc2e2f29736 (re)

An uncompressed clone transfers obsolete changesets and markers

  $ hg clone -U --uncompressed ssh://user@dummy/$TESTTMP/server clone-obsolete2
  streaming all changes
  5 files to transfer, * KB of data (glob)
  transferred 1.19 KB in 0.0 seconds (*) (glob)
  searching for changes
  no changes found
  1 new obsolescence markers

The pushlog should pull cleanly because hidden changesets are present locally

  $ hg -R clone-obsolete2 --config extensions.pushlog=$TESTDIR/hgext/pushlog pull
  pulling from ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  added 4 pushes

  $ dumppushlog clone-obsolete2
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: ae13d9da6966307c98b60987fb4fedc2e2f29736 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 2; Node: 80c2c663cb8364f6898662a8379cb25df3ebe719 (re)
  ID: 4; user: hguser; Date: \d+; Rev: 3; Node: a129f82339bb933c4d72353c44bb29eb685f3d1e (re)
