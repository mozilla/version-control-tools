#require hg37+

bundleclone wraps localrepository.clone, which doesn't exist in Mercurial 3.7+.
This test verifies the extension no-ops on modern hg versions.

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bundleclone = $TESTDIR/hgext/bundleclone
  > EOF

  $ hg init server
  $ cd server
  $ touch foo
  $ hg -q commit -A -m 'add foo'
  $ touch bar
  $ hg -q commit -A -m 'add bar'

  $ hg serve -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS
  $ touch .hg/bundleclone.manifest
  $ cd ..

  $ hg -v clone http://localhost:$HGPORT client1
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  updating to branch default
  resolving manifests
  getting bar
  getting foo
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

