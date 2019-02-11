If there is a remote named `try`, `push-to-try` defaults to pushing to it.

  $ cat >> $HGRCPATH << EOF
  > [paths]
  > try = $TESTTMP/remote
  > [extensions]
  > push-to-try = $TESTDIR/hgext/push-to-try
  > EOF

  $ hg init remote
  $ hg clone remote local
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd local
  $ touch foo
  $ hg -q commit -A -m initial

  $ hg push-to-try -m 'try: syntax'
  Creating temporary commit for remote...
  pushing to $TESTTMP/remote
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 1 files
  push complete
  temporary commit removed, repository restored
