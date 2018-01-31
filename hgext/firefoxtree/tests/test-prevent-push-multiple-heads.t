  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > firefoxtree = $TESTDIR/hgext/firefoxtree
  > EOF

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ PUSHABLE_HTTP=1 makefirefoxreposserver root $HGPORT1
  $ installfakereposerver $HGPORT $TESTTMP/root
  $ populatedummydata root >/dev/null

  $ hg init root/non-canonical

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

Pushing multiple heads will result in abort

  $ hg push --force -r 0:tip central
  pushing to ssh://user@dummy/$TESTTMP/root/mozilla-central
  searching for changes
  abort: cannot push multiple heads to a Firefox tree; limit pushed revisions using the -r argument
  [255]

Pushing multiple heads to a non-canonical tree is OK

  $ hg push --force ssh://user@dummy/$TESTTMP/root/non-canonical
  pushing to ssh://user@dummy/$TESTTMP/root/non-canonical
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 4 changesets with 4 changes to 1 files (+1 heads)

We can still push multiple heads to non-Firefox repos

  $ rm .hg/IS_FIREFOX_REPO
  $ hg push --force -r 0:tip http://localhost:$HGPORT1/mozilla-central
  pushing to http://localhost:$HGPORT1/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files (+1 heads)
