#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir > /dev/null 2>&1

  $ hg -R repo push
  pushing to http://localhost:$HGPORT/overlay-dest
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 3 changes to 3 files

Add new changesets in both source and dest

  $ cd server/overlay-source
  $ echo new-source1 > new-source
  $ hg -q commit -A -m 'new source 1'
  $ echo new-source > new-source
  $ hg commit -m 'new source 2'
  $ cd ../overlay-dest
  $ hg -q up tip
  $ echo new-dest1 > new-dest
  $ hg -q commit -A -m 'new dest 1'
  $ echo new-dest2 > new-dest
  $ hg commit -m 'new dest 2'
  $ cd ../..

Overlay with both new dest and source will pull dest and apply new sources

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 05e6f02d8e8c
  pulling http://localhost:$HGPORT/overlay-dest to obtain 05e6f02d8e8c
  executing: hg pull -r 05e6f02d8e8c http://localhost:$HGPORT/overlay-dest
  hg> pulling from http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 2 changesets with 2 changes to 1 files
  hg> (run 'hg update' to get a working copy)
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 05e6f02d8e8c47eea023572bb08ad29f878936df
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/repo/.hg/localhost~3a*__overlay-source (glob)
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 2 changesets with 2 changes to 1 files
  hg> d92cc0ff6f1a already processed as eaf64eb11964; skipping 2/4 revisions
  hg> 03f307e60484 -> 1f5ce5f190a2: new source 1
  hg> fabffa48ea9f -> fc9f4bdac504: new source 2
  2 new changesets; new tip is fc9f4bdac504bf7da1920a4449b012837e99c152
