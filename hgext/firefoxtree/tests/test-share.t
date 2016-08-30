  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > share =
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ firefoxtreesexists() {
  >   [ -f .hg/firefoxtrees ] && echo "firefoxtrees exists" || echo "no firefoxtrees"
  > }

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
  $ populatedummydata root > /dev/null

Create the base repository

  $ hg init base
  $ cd base
  $ touch .hg/IS_FIREFOX_REPO

  $ hg -q pull central
  $ hg -q pull integration

  $ hg fxheads
  1:994ec05999da central Bug 457 - second commit to m-c; r=ted
  4:3057abf99ee2 fx-team Bug 460 - Create bar on fx-team
  3:1b348279b0e9 inbound Bug 459 - Second commit to inbound

  $ cd ..

A repository sharing the store should inherit the tree tags

  $ hg share base shared
  updating working directory
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd shared
  $ touch .hg/IS_FIREFOX_REPO
  $ firefoxtreesexists
  no firefoxtrees

  $ cat .hg/shared
  firefoxtrees

  $ hg fxheads
  1:994ec05999da central Bug 457 - second commit to m-c; r=ted
  4:3057abf99ee2 fx-team Bug 460 - Create bar on fx-team
  3:1b348279b0e9 inbound Bug 459 - Second commit to inbound

Now pull another repo and verify firefoxtrees on the share source is updated

  $ cd ../root/releases/mozilla-beta
  $ hg -q pull ../../mozilla-central
  $ cd ../../../shared

  $ hg -q pull beta
  $ firefoxtreesexists
  no firefoxtrees
  $ hg fxheads
  1:994ec05999da beta central Bug 457 - second commit to m-c; r=ted
  4:3057abf99ee2 fx-team Bug 460 - Create bar on fx-team
  3:1b348279b0e9 inbound Bug 459 - Second commit to inbound

Now do a variation that also shared bookmarks
(to test we don't interfere with it)

  $ cd ..
  $ hg share -B base shared2
  updating working directory
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd shared2
  $ touch .hg/IS_FIREFOX_REPO
  $ cat .hg/shared
  bookmarks
  firefoxtrees

  $ hg fxheads
  1:994ec05999da beta central Bug 457 - second commit to m-c; r=ted
  4:3057abf99ee2 fx-team Bug 460 - Create bar on fx-team
  3:1b348279b0e9 inbound Bug 459 - Second commit to inbound
