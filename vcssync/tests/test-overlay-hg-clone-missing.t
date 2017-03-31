#require hg41+

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

Local clone will be created if necessary

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   local_path --into subdir
  local_path does not exist; cloning http://localhost:$HGPORT/overlay-dest
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/local_path/.hg/localhost~3a*__overlay-source (glob)
  hg> requesting all changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 2 changesets with 3 changes to 3 files
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1

Again for good measure

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   local_path --into subdir
  executing: hg strip --no-backup -r 'not public()'
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
