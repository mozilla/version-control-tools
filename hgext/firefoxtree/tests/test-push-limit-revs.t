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

  $ echo 'push1' > foo
  $ hg commit -m 'Bug 789 - Testing push1'

  $ hg up central
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 'push2' > foo
  $ hg commit -m 'Bug 790 - Testing push2'
  created new head

Outgoing with no -r argument will limit to .

  $ hg out central
  no revisions specified; using . to avoid inspecting multiple heads
  comparing with central
  searching for changes
  changeset:   3:d455de7ec717
  tag:         tip
  parent:      1:994ec05999da
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Bug 790 - Testing push2
  

Pushing with no -r argument will limit to .

  $ hg push central
  pushing to ssh://user@dummy/$TESTTMP/root/mozilla-central
  no revisions specified to push; using . to avoid pushing multiple heads
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files

Outgoing should be limited, so no output expected

  $ hg out central
  no revisions specified; using . to avoid inspecting multiple heads
  comparing with central
  searching for changes
  no changes found
  [1]
