  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
  $ populatedummydata root > /dev/null

  $ hg init simple-repo
  $ cd simple-repo
  $ touch .hg/IS_FIREFOX_REPO

  $ hg -q pull central
  $ hg -q pull inbound

Add an entry for a missing node

  $ cat >> .hg/firefoxtrees << EOF
  > 
  > autoland 0000000000111111111122222222223333333333
  > EOF

  $ hg log -r 'fxheads()' -T '{node}\n'
  994ec05999daf04fb3c01a8cb0dea1458a7d4d3d
  1b348279b0e9b3c29568b6abc8a1776a68d39261

  $ cd ..

The same test but for a repository that uses obsolescence

  $ hg init obs-repo
  $ cd obs-repo
  $ touch .hg/IS_FIREFOX_REPO

  $ cat >> .hg/hgrc << EOF
  > [experimental]
  > evolution = createmarkers
  > EOF

  $ hg -q pull central
  $ hg -q pull inbound

Prune the changeset associated with inbound

  $ hg phase --draft --force -r 0:tip
  $ hg debugobsolete 1b348279b0e9b3c29568b6abc8a1776a68d39261
  obsoleted 1 changesets (?)

  $ hg log -r 'fxheads()' -T '{node}\n'
  994ec05999daf04fb3c01a8cb0dea1458a7d4d3d
