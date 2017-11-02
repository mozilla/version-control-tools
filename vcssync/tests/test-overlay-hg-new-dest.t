#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir > /dev/null 2>&1

New changeset in dest will be pulled and overlay will reperformed on it

  $ cd server/overlay-dest
  $ echo new-dest > new-dest
  $ hg -q commit -A -m 'new changeset in dest'
  $ cd ../..

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir
  executing: hg strip --no-backup -r 'not public()'
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 7d4c615194ec
  pulling http://localhost:$HGPORT/overlay-dest to obtain 7d4c615194ec
  executing: hg pull -r 7d4c615194ec http://localhost:$HGPORT/overlay-dest
  hg> pulling from http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 1 changesets with 1 changes to 1 files
  hg> (run 'hg update' to get a working copy)
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 7d4c615194ec642cb4f0ff9be89a536db8075e02
  hg> 76f0fc85e215 -> adc6459339d2: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> d35c1c7442f0: add dir0/file0
  2 new changesets; new tip is d35c1c7442f0f2ed4478ca1e1bafebb4ac98c9e3

  $ hg -R repo log -G -T '{node|short} {desc}'
  o  d35c1c7442f0 add dir0/file0
  |
  o  adc6459339d2 initial - add source-file0 and source-file1
  |
  o  7d4c615194ec new changeset in dest
  |
  o  88dd2a5005e6 initial in dest
  

