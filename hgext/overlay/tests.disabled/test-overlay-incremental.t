  $ . $TESTDIR/hgext/overlay/tests/helpers.sh

  $ hg init source
  $ cd source
  $ echo 0 > foo
  $ hg -q commit -A -m 'source commit 0'
  $ echo 1 > foo
  $ hg commit -m 'source commit 1'
  $ hg serve -d --pid-file hg.pid -p $HGPORT
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ hg init dest
  $ cd dest
  $ touch root
  $ hg -q commit -A -m 'dest commit 0'

  $ hg overlay http://localhost:$HGPORT --into subdir
  pulling http://localhost:$HGPORT into $TESTTMP/dest/.hg/localhost~3a* (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  new changesets 00f6e41c0e85:c71ec8379b05 (?)
  00f6e41c0e85 -> 680a5f65e0c3: source commit 0
  c71ec8379b05 -> 81f80944e32d: source commit 1

Incremental overlay will no-op since no new changesets

  $ hg overlay http://localhost:$HGPORT --into subdir
  c71ec8379b05 already processed as 81f80944e32d; skipping 2/2 revisions
  no source revisions left to process

New changeset in source should get applied as expected

  $ cd ../source
  $ echo 2 > foo
  $ hg commit -m 'source commit 2'
  $ cd ../dest
  $ hg overlay http://localhost:$HGPORT --into subdir
  pulling http://localhost:$HGPORT into $TESTTMP/dest/.hg/localhost~3a* (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 60f2998d907d (?)
  c71ec8379b05 already processed as 81f80944e32d; skipping 2/3 revisions
  60f2998d907d -> 50fab12f8664: source commit 2

  $ hg log -G -T '{node|short} {desc}'
  o  50fab12f8664 source commit 2
  |
  o  81f80944e32d source commit 1
  |
  o  680a5f65e0c3 source commit 0
  |
  @  cb699e5348c1 dest commit 0
  

New changeset in source and dest results in being applied on latest in dest

  $ cd ../source
  $ echo 3 > foo
  $ hg commit -m 'source commit 3'
  $ cd ../dest

  $ hg -q up tip
  $ echo 'source 2' > root
  $ hg commit -m 'dest commit 1'

  $ hg overlay http://localhost:$HGPORT --into subdir
  pulling http://localhost:$HGPORT into $TESTTMP/dest/.hg/localhost~3a* (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 2d54a6016dfe (?)
  60f2998d907d already processed as 50fab12f8664; skipping 3/4 revisions
  2d54a6016dfe -> 3b62843da7a4: source commit 3

  $ hg log -G -T '{node|short} {desc}'
  o  3b62843da7a4 source commit 3
  |
  @  504ce2b98c14 dest commit 1
  |
  o  50fab12f8664 source commit 2
  |
  o  81f80944e32d source commit 1
  |
  o  680a5f65e0c3 source commit 0
  |
  o  cb699e5348c1 dest commit 0
  

Overlaying onto a head without all changesets will pick up where it left off

  $ hg -q up 81f80944e32d
  $ echo 'head 1' > root
  $ hg commit -m 'head 1'
  created new head
  $ hg overlay http://localhost:$HGPORT --into subdir
  c71ec8379b05 already processed as 81f80944e32d; skipping 2/4 revisions
  60f2998d907d -> 13ddb87af500: source commit 2
  2d54a6016dfe -> b06ac9515e0a: source commit 3

  $ hg log -G -T '{node|short} {desc}'
  o  b06ac9515e0a source commit 3
  |
  o  13ddb87af500 source commit 2
  |
  @  9af62c37d9de head 1
  |
  | o  3b62843da7a4 source commit 3
  | |
  | o  504ce2b98c14 dest commit 1
  | |
  | o  50fab12f8664 source commit 2
  |/
  o  81f80944e32d source commit 1
  |
  o  680a5f65e0c3 source commit 0
  |
  o  cb699e5348c1 dest commit 0
  

Source rev that has already been overlayed will fail

  $ hg overlay http://localhost:$HGPORT 'c71ec8379b05::' --into subdir
  2d54a6016dfe already processed as b06ac9515e0a; skipping 3/3 revisions
  no source revisions left to process

Source rev starting at next changeset will work

  $ echo 'head 1 commit 2' > root
  $ hg commit -m 'head 1 commit 2'
  created new head
  $ hg overlay http://localhost:$HGPORT '60f2998d907d::' --into subdir
  60f2998d907d -> 0a78f301953e: source commit 2
  2d54a6016dfe -> 4c9b5c9fec78: source commit 3

  $ hg log -G -T '{node|short} {desc}'
  o  4c9b5c9fec78 source commit 3
  |
  o  0a78f301953e source commit 2
  |
  @  c99f42f18be8 head 1 commit 2
  |
  | o  b06ac9515e0a source commit 3
  | |
  | o  13ddb87af500 source commit 2
  |/
  o  9af62c37d9de head 1
  |
  | o  3b62843da7a4 source commit 3
  | |
  | o  504ce2b98c14 dest commit 1
  | |
  | o  50fab12f8664 source commit 2
  |/
  o  81f80944e32d source commit 1
  |
  o  680a5f65e0c3 source commit 0
  |
  o  cb699e5348c1 dest commit 0
  

Selecting a source changeset that is missing parents in dest will fail

  $ echo 'head 1 commit 3' > root
  $ hg commit -m 'head 1 commit 3'
  created new head
  $ hg overlay http://localhost:$HGPORT '2d54a6016dfe::' --into subdir
  abort: first source changeset (2d54a6016dfe) is not a child of last overlayed changeset (c71ec8379b05)
  [255]
