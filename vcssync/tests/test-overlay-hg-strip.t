#require hg41+

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

Seed local clone

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir > /dev/null 2>&1

  $ cd repo

Nuke the overlayed changesets b/c they interfere with next test

  $ hg -q --config extensions.strip= strip -r 'not public()'
  $ hg log -G -T '{node|short} {desc}'
  o  88dd2a5005e6 initial in dest
  

Add some draft changesets that should be stripped

  $ touch local0
  $ hg -q commit -A -m 'add local0'
  $ touch local1
  $ hg -q commit -A -m 'add local1'

Verify draft changesets are stripped

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   . --into subdir
  executing: hg strip --no-backup -r 'not public()'
  hg> 0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1

  $ hg log -G -T '{node|short} {desc}'
  o  eaf64eb11964 add dir0/file0
  |
  o  67c9543981c6 initial - add source-file0 and source-file1
  |
  o  88dd2a5005e6 initial in dest
  
