  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
  $ populatedummydata root >/dev/null

Create a unified repository with tags

  $ cd root/unified
  $ cat >> .hg/hgrc << EOF
  > [firefoxtree]
  > servetags = True
  > EOF

  $ hg pull http://localhost:$HGPORT/mozilla-central
  pulling from http://localhost:$HGPORT/mozilla-central
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  (run 'hg update' to get a working copy)
  $ hg pull http://localhost:$HGPORT/integration/mozilla-inbound
  pulling from http://localhost:$HGPORT/integration/mozilla-inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  (run 'hg update' to get a working copy)
  $ hg pull http://localhost:$HGPORT/integration/fx-team
  pulling from http://localhost:$HGPORT/integration/fx-team
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ cd ../..

Pulling from the unified repo will pull the Firefox tree tags

  $ hg init repo
  $ cd repo
  $ touch .hg/IS_FIREFOX_REPO
  $ hg pull http://localhost:$HGPORT/unified
  pulling from http://localhost:$HGPORT/unified
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 5 changes to 2 files (+1 heads)
  updated firefox tree tag central
  updated firefox tree tag fx-team
  updated firefox tree tag inbound
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ cat .hg/localtags
  994ec05999daf04fb3c01a8cb0dea1458a7d4d3d central
  3057abf99ee2f9d810425f7eb1828f408be2c71f fx-team
  1b348279b0e9b3c29568b6abc8a1776a68d39261 inbound
  $ cd ..

Doing an incremental pull will print commit count change

  $ cd root/integration/mozilla-inbound
  $ echo 'incremental-1' > foo
  $ hg commit -m 'Incremental 1'
  $ echo 'incremental-2' > foo
  $ hg commit -m 'Incremental 2'
  $ cd ../fx-team
  $ echo 'incremental-3' > foo
  $ hg commit -m 'Incremental 3'
  $ cd ../../unified
  $ hg pull http://localhost:$HGPORT/integration/mozilla-inbound > /dev/null
  $ hg pull http://localhost:$HGPORT/integration/fx-team > /dev/null

  $ cd ../../repo
  $ hg pull http://localhost:$HGPORT/unified
  pulling from http://localhost:$HGPORT/unified
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  updated firefox tree tag fx-team (+1 commits)
  updated firefox tree tag inbound (+2 commits)
  (run 'hg update' to get a working copy)
  $ cat .hg/localtags
  994ec05999daf04fb3c01a8cb0dea1458a7d4d3d central
  a4521c3750458afd82406ac87977b3fdc2fdc62a fx-team
  388ff24b5456e83175491ae321bceb89aad2259f inbound
