  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > pushrebase = $TESTDIR/hgext/pushrebase
  > 
  > [experimental]
  > bundle2-exp = True
  > EOF

Stand up a server

  $ hg init server
  $ cd server
  $ cat > .hg/hgrc << EOF
  > [web]
  > allow_push = *
  > push_ssl = False
  > EOF

  $ echo initial > foo
  $ hg -q commit -A -m initial

  $ echo first > foo
  $ hg commit -m 'first commit'

  $ hg serve -d --pid-file hg.pid -p $HGPORT
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Make a clone and create divergent history

  $ hg clone -r 0 http://localhost:$HGPORT client
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ echo bar > bar
  $ hg -q commit -A -m 'unrelated divergent commit'

  $ hg log -G
  @  changeset:   1:58917bc08918
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     unrelated divergent commit
  |
  o  changeset:   0:55482a6fb4b1
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

Push should complain about new head

  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote has heads on branch 'default' that are not known locally: 934496297d08
  abort: push creates new remote head 58917bc08918!
  (pull and merge or see "hg help push" for details about pushing new heads)
  [255]

Push rebase should work

  $ hg push --onto default
  pushing to http://localhost:$HGPORT/
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 2 files (+1 heads)

It leaves an orphan head, but that's how pushrebase works without
obsolescence :/

  $ hg log -G
  o  changeset:   3:0096fc004608
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     unrelated divergent commit
  |
  o  changeset:   2:934496297d08
  |  parent:      0:55482a6fb4b1
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     first commit
  |
  | @  changeset:   1:58917bc08918
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     unrelated divergent commit
  |
  o  changeset:   0:55482a6fb4b1
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

  $ cd ../server
  $ hg log -G
  o  changeset:   2:0096fc004608
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     unrelated divergent commit
  |
  @  changeset:   1:934496297d08
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     first commit
  |
  o  changeset:   0:55482a6fb4b1
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  
