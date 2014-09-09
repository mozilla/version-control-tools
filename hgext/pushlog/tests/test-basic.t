  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurepushlog server

  $ hg init client
  $ cd client
  $ dumppushlog server
  pushlog database does not exist: $TESTTMP/server/.hg/pushlog2.db
  [1]

Pushing single changesets at a time works

  $ export USER=hguser
  $ touch foo
  $ hg commit -A -m 'Add foo'
  adding foo
  $ hg log
  changeset:   0:12cb2e907074
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Add foo
  
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.

  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 12cb2e907074dd3f8a985a0bb3713836bae731d8 (re)

  $ echo '2' > foo
  $ hg commit -m 'Update foo'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.

  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 12cb2e907074dd3f8a985a0bb3713836bae731d8 (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: 6e7d3c626e4989d83a04858aa53fb650d828ab23 (re)

Verify the pushlog database is group writable after pushing

  >>> import os, stat
  >>> st = os.stat('../server/.hg/pushlog2.db')
  >>> assert st.st_mode & stat.S_IWGRP == stat.S_IWGRP

Pushing multiple changesets at a time works

  $ echo '3' > foo
  $ hg commit -m '3'
  $ echo '4' > foo
  $ hg commit -m '4'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.

  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 12cb2e907074dd3f8a985a0bb3713836bae731d8 (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: 6e7d3c626e4989d83a04858aa53fb650d828ab23 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 2; Node: 5276547e6f081e8aabd9d49852587caaa54a19b6 (re)
  ID: 3; user: hguser; Date: \d+; Rev: 3; Node: 241ebd3a5ff9e76aed375695521d83dbfa2531e2 (re)

Multiple users are recognized

  $ hg init ../users
  $ configurepushlog ../users
  $ hg push -r 1 ../users >/dev/null
  $ export USER=another
  $ hg push ../users >/dev/null
  $ dumppushlog users
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 12cb2e907074dd3f8a985a0bb3713836bae731d8 (re)
  ID: 1; user: hguser; Date: \d+; Rev: 1; Node: 6e7d3c626e4989d83a04858aa53fb650d828ab23 (re)
  ID: 2; user: another; Date: \d+; Rev: 2; Node: 5276547e6f081e8aabd9d49852587caaa54a19b6 (re)
  ID: 2; user: another; Date: \d+; Rev: 3; Node: 241ebd3a5ff9e76aed375695521d83dbfa2531e2 (re)
  $ export USER=hguser

Pushing to an empty db file works (bug 466149)

  $ hg init ../empty
  $ configurepushlog ../empty
  $ touch ../empty/.hg/pushlog2.db
  $ hg push ../empty
  pushing to ../empty
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 4 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.

  $ dumppushlog empty
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 12cb2e907074dd3f8a985a0bb3713836bae731d8 (re)
  ID: 1; user: hguser; Date: \d+; Rev: 1; Node: 6e7d3c626e4989d83a04858aa53fb650d828ab23 (re)
  ID: 1; user: hguser; Date: \d+; Rev: 2; Node: 5276547e6f081e8aabd9d49852587caaa54a19b6 (re)
  ID: 1; user: hguser; Date: \d+; Rev: 3; Node: 241ebd3a5ff9e76aed375695521d83dbfa2531e2 (re)

Pushing to a locked DB errors out (bug 508863)

  $ cat >> lockdb.py << EOF
  > import os, sqlite3, sys, time
  > conn = sqlite3.connect(sys.argv[1])
  > conn.execute('INSERT INTO pushlog (user, date) VALUES("user", 0)')
  > while not os.path.exists(sys.argv[2]):
  >    time.sleep(0.1)
  > EOF

  $ hg init ../locked
  $ configurepushlog ../locked
  $ hg push -r 0 ../locked >/dev/null
  $ python lockdb.py ../locked/.hg/pushlog2.db unlock &
  $ pid=$!
  $ echo $pid >> $DAEMON_PIDS
  $ hg push ../locked
  pushing to ../locked
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Error inserting into pushlog. Please retry your push.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.pushlog hook failed
  [255]
  $ touch unlock

  $ hg push -r 1 ../locked
  pushing to ../locked
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  Trying to insert into pushlog.
  Please do not interrupt...
  Inserted into the pushlog db successfully.

  $ dumppushlog locked
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 12cb2e907074dd3f8a985a0bb3713836bae731d8 (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: 6e7d3c626e4989d83a04858aa53fb650d828ab23 (re)
