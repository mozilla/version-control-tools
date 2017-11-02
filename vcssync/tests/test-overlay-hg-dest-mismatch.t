#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into destdir > /dev/null 2>&1

  $ hg -R repo push
  pushing to http://localhost:$HGPORT/overlay-dest
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 3 changes to 3 files

Create a changeset in destination directory with unexpected changes

  $ cd server/overlay-dest
  $ hg -q up tip
  $ echo unwanted > destdir/unwanted-file
  $ hg -q commit -A -m 'add unwanted file to destdir'
  $ cd ../overlay-source
  $ echo new > new-file
  $ hg -q commit -A -m 'new source changeset'
  $ cd ../..

Attempting an incremental overlay will fail due to state mismatch in
destination directory

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into destdir
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 868ababf5511
  pulling http://localhost:$HGPORT/overlay-dest to obtain 868ababf5511
  executing: hg pull -r 868ababf5511 http://localhost:$HGPORT/overlay-dest
  hg> pulling from http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 1 changesets with 1 changes to 1 files
  hg> (run 'hg update' to get a working copy)
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into destdir -d 868ababf5511149027ca40e5de059e3a88c32a3c
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/repo/.hg/localhost~3a*__overlay-source (glob)
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 1 changesets with 1 changes to 1 files
  hg> d92cc0ff6f1a already processed as 1467125e7dd1; skipping 2/3 revisions
  hg> abort: files mismatch between source and destination: unwanted-file
  hg> (destination must match previously imported changeset (d92cc0ff6f1a) exactly)
  abort: hg command failed
  [1]

We can correct the issue by reconciling the state in dest

  $ cd server/overlay-dest
  $ hg rm destdir/unwanted-file
  $ hg commit -m 'remove unwanted-file from dest'
  $ cd ../..

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into destdir
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 0a081fabba0d
  pulling http://localhost:$HGPORT/overlay-dest to obtain 0a081fabba0d
  executing: hg pull -r 0a081fabba0d http://localhost:$HGPORT/overlay-dest
  hg> pulling from http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 1 changesets with 0 changes to 0 files
  hg> (run 'hg update' to get a working copy)
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into destdir -d 0a081fabba0d02fd0ebead1c5ce1256da71866ea
  hg> d92cc0ff6f1a already processed as 1467125e7dd1; skipping 2/3 revisions
  hg> 74beb83990f0 -> 5065bae0b434: new source changeset
  1 new changesets; new tip is 5065bae0b434149f4937727d9715b9e1490bb51a
