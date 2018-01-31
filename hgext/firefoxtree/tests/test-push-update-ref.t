  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT $TESTTMP/root
  $ populatedummydata root >/dev/null

  $ hg init repo1
  $ cd repo1
  $ touch .hg/IS_FIREFOX_REPO

  $ hg pull central
  pulling from central
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  new changesets b772b099dda6:994ec05999da (?)
  (run 'hg update' to get a working copy)
  $ hg up central
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Pushing to a known tree should update the local tag

  $ hg fxheads
  1:994ec05999da central Bug 457 - second commit to m-c; r=ted

  $ cat .hg/firefoxtrees
  central 994ec05999daf04fb3c01a8cb0dea1458a7d4d3d (no-eol)

  $ echo 'push1' > foo
  $ hg commit -m 'Bug 789 - Testing push1'

  $ hg push -r . central
  pushing to ssh://user@dummy/$TESTTMP/root/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files

  $ hg fxheads
  2:683791dab932 central Bug 789 - Testing push1

  $ cat .hg/firefoxtrees
  central 683791dab9323f2f3c7730260806c9cf8560995f (no-eol)
