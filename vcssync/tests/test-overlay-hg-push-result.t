#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

--result-push-url will push results after overlay

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir --result-push-url http://localhost:$HGPORT/overlay-dest
  repo does not exist; cloning http://localhost:$HGPORT/overlay-dest
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  new changesets 88dd2a5005e6
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/repo/.hg/localhost~3a*__overlay-source (glob)
  hg> requesting all changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 2 changesets with 3 changes to 3 files
  hg> new changesets 76f0fc85e215:d92cc0ff6f1a
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  pushing 2 new changesets on head eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 to http://localhost:$HGPORT/overlay-dest
  1:67c9543981c6: initial - add source-file0 and source-file1
  2:eaf64eb11964: add dir0/file0
  executing: hg push -r eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 http://localhost:$HGPORT/overlay-dest
  hg> pushing to http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> remote: adding changesets
  hg> remote: adding manifests
  hg> remote: adding file changes
  hg> remote: added 2 changesets with 3 changes to 3 files

No-op after pushing results

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir --result-push-url http://localhost:$HGPORT/overlay-dest
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> eaf64eb11964
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  hg> d92cc0ff6f1a already processed as eaf64eb11964; skipping 2/2 revisions
  hg> no source revisions left to process
  no changesets overlayed

Incremental overlay + push works

  $ cd server/overlay-dest
  $ hg -q up tip
  $ echo 1 > new-dest
  $ hg -q commit -A -m 'new in dest 1'
  $ echo 2 > new-dest
  $ hg commit -m 'new in dest 2'
  $ cd ../overlay-source
  $ echo 1 > new-source
  $ hg -q commit -A -m 'new in source 1'
  $ echo 2 > new-source
  $ hg commit -m 'new in source 2'
  $ cd ../..

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir --result-push-url http://localhost:$HGPORT/overlay-dest
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 9407bbd2ed9a
  pulling http://localhost:$HGPORT/overlay-dest to obtain 9407bbd2ed9a
  executing: hg pull -r 9407bbd2ed9a http://localhost:$HGPORT/overlay-dest
  hg> pulling from http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 2 changesets with 2 changes to 1 files
  hg> new changesets f5e3c64b366d:9407bbd2ed9a
  hg> (run 'hg update' to get a working copy)
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 9407bbd2ed9ae87d1412db63ccbdc88dfc244d8b
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/repo/.hg/localhost~3a*__overlay-source (glob)
  hg> searching for changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 2 changesets with 2 changes to 1 files
  hg> new changesets b819368ed1b8:8daaa17f19e3
  hg> d92cc0ff6f1a already processed as eaf64eb11964; skipping 2/4 revisions
  hg> b819368ed1b8 -> 065d6faac6a8: new in source 1
  hg> 8daaa17f19e3 -> a8fc26f818c2: new in source 2
  2 new changesets; new tip is a8fc26f818c2ec9874d098d3ba1ccbbde7abfab6
  pushing 2 new changesets on head a8fc26f818c2ec9874d098d3ba1ccbbde7abfab6 to http://localhost:$HGPORT/overlay-dest
  5:065d6faac6a8: new in source 1
  6:a8fc26f818c2: new in source 2
  executing: hg push -r a8fc26f818c2ec9874d098d3ba1ccbbde7abfab6 http://localhost:$HGPORT/overlay-dest
  hg> pushing to http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> remote: adding changesets
  hg> remote: adding manifests
  hg> remote: adding file changes
  hg> remote: added 2 changesets with 2 changes to 1 files
