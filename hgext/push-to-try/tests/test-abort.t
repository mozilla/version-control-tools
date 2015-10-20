Abort during transaction will roll back gracefully

  $ cat >> $HGRCPATH << EOF
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

  $ hg --config hooks.preoutgoing.fail=false push-to-try -m 'try: syntax' -s ../remote
  Creating temporary commit for remote...
  pushing to ../remote
  searching for changes
  temporary commit removed, repository restored
  abort: preoutgoing.fail hook exited with status 1
  [255]

  $ hg recover
  no interrupted transaction available
  [1]
