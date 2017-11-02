#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir > /dev/null 2>&1

  $ hg -R repo push
  pushing to http://localhost:$HGPORT/overlay-dest
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 3 changes to 3 files

New changeset in source will be incrementally applied

  $ cd server/overlay-source
  $ echo new-source > new-source
  $ hg -q commit -A -m 'add new-source'
  $ cd ../..

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> eaf64eb11964
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/repo/.hg/localhost~3a*__overlay-source (glob)
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 1 changesets with 1 changes to 1 files
  hg> d92cc0ff6f1a already processed as eaf64eb11964; skipping 2/3 revisions
  hg> becea3ef593b -> 21cdbe8f0971: add new-source
  1 new changesets; new tip is 21cdbe8f0971d8ec7d64fa34a59ea69e2936ce2e

  $ hg -R repo log -G -T '{node|short} {desc}'
  o  21cdbe8f0971 add new-source
  |
  o  eaf64eb11964 add dir0/file0
  |
  o  67c9543981c6 initial - add source-file0 and source-file1
  |
  o  88dd2a5005e6 initial in dest
  

  $ hg -R repo push
  pushing to http://localhost:$HGPORT/overlay-dest
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files

No-op after publish

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 21cdbe8f0971
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 21cdbe8f0971d8ec7d64fa34a59ea69e2936ce2e
  hg> becea3ef593b already processed as 21cdbe8f0971; skipping 3/3 revisions
  hg> no source revisions left to process
  no changesets overlayed
