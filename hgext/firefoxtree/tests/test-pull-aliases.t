  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
  $ populatedummydata root >/dev/null

We can pull from the special multiple tree aliases

  $ hg init repo1
  $ cd repo1
  $ touch .hg/IS_FIREFOX_REPO

  $ hg pull integration
  pulling from inbound
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 4 changes to 1 files
  (run 'hg update' to get a working copy)
  pulling from fx-team
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  pulling from services
  searching for changes
  no changes found
  pulling from build
  searching for changes
  no changes found
  pulling from b2ginbound
  searching for changes
  no changes found

  $ hg fxheads
  1:994ec05999da b2ginbound build services Bug 457 - second commit to m-c; r=ted
  1:994ec05999da b2ginbound build services Bug 457 - second commit to m-c; r=ted
  4:3057abf99ee2 fx-team tip Bug 460 - Create bar on fx-team
  3:1b348279b0e9 inbound Bug 459 - Second commit to inbound
  1:994ec05999da b2ginbound build services Bug 457 - second commit to m-c; r=ted

  $ cd ..

fxtrees is a special alias that expands to trees that have been pulled before

  $ hg init repo2
  $ cd repo2
  $ touch .hg/IS_FIREFOX_REPO

  $ hg -q pull inbound
  $ hg -q pull fx-team

  $ hg fxheads
  4:3057abf99ee2 fx-team tip Bug 460 - Create bar on fx-team
  3:1b348279b0e9 inbound Bug 459 - Second commit to inbound

  $ hg pull fxtrees
  pulling from fx-team
  searching for changes
  no changes found
  pulling from inbound
  searching for changes
  no changes found

  $ hg pull central
  pulling from central
  searching for changes
  no changes found

  $ hg pull fxtrees
  pulling from central
  searching for changes
  no changes found
  pulling from fx-team
  searching for changes
  no changes found
  pulling from inbound
  searching for changes
  no changes found
