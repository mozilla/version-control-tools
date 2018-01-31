  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
  $ populatedummydata root > /dev/null

  $ hg init repo1
  $ cd repo1
  $ touch .hg/IS_FIREFOX_REPO
  $ hg -q pull central

localtags entries for fxtrees should get pruned on next firefoxtrees write

  $ cat > .hg/localtags << EOF
  > 994ec05999daf04fb3c01a8cb0dea1458a7d4d3d inbound
  > 994ec05999daf04fb3c01a8cb0dea1458a7d4d3d fx-team
  > 994ec05999daf04fb3c01a8cb0dea1458a7d4d3d central
  > 994ec05999daf04fb3c01a8cb0dea1458a7d4d3d testlocal
  > EOF

  $ hg pull inbound
  pulling from inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  new changesets 01d6e2d31f88:1b348279b0e9 (?)
  (run 'hg update' to get a working copy)

  $ cat .hg/localtags
  994ec05999daf04fb3c01a8cb0dea1458a7d4d3d testlocal (no-eol)
