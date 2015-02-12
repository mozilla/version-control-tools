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

Can pull from an alias

  $ hg pull central
  pulling from central
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  (run 'hg update' to get a working copy)

  $ hg pull inbound
  pulling from inbound
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  (run 'hg update' to get a working copy)

Pulled Firefox repos show up as tags

  $ hg log
  changeset:   3:1b348279b0e9
  tag:         inbound
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Bug 459 - Second commit to inbound
  
  changeset:   2:01d6e2d31f88
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Bug 458 - Commit to inbound
  
  changeset:   1:994ec05999da
  tag:         central
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Bug 457 - second commit to m-c; r=ted
  
  changeset:   0:b772b099dda6
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Bug 456 - initial commit to m-c; r=gps
  

hg fxheads displays known tree commits

  $ hg fxheads
  1:994ec05999da central Bug 457 - second commit to m-c; r=ted
  3:1b348279b0e9 inbound tip Bug 459 - Second commit to inbound

hg fxheads revset gives known tree commits

  $ hg log -r "fxheads()"
  changeset:   1:994ec05999da
  tag:         central
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Bug 457 - second commit to m-c; r=ted
  
  changeset:   3:1b348279b0e9
  tag:         inbound
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Bug 459 - Second commit to inbound
  

{fxheads} template keyword works

  $ hg log -T '{rev} {fxheads}\n'
  3 inbound
  2 
  1 central
  0 

{fxheads} with multiple values

  $ hg -q pull b2ginbound
  $ hg log -T '{rev} {join(fxheads, " ")}\n'
  3 inbound
  2 
  1 b2ginbound central
  0 
