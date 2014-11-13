  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
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
  (run 'hg update' to get a working copy)
  $ hg up central
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Pushing to a known tree should update the local tag

  $ hg fxheads
  1:994ec05999da central tip Bug 457 - second commit to m-c; r=ted

  $ echo 'push1' > foo
  $ hg commit -m 'Bug 789 - Testing push1'

  $ hg push -r . central
  pushing to central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files

  $ hg fxheads
  2:683791dab932 central tip Bug 789 - Testing push1
