#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir >/dev/null 2>&1

Create a new dest-like repo and add a changeset to it.
This simulates losing a push race to another client.

  $ hg clone server/overlay-dest server/push-race
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd server/push-race
  $ echo raced > race
  $ hg -q commit -A -m 'simulate push race'
  $ cd ../..

Now push to the dest-like repo in a way that would create a new head

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir --result-push-url http://localhost:$HGPORT/push-race
  executing: hg strip --no-backup -r 'not public()'
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  pushing 2 new changesets on head eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 to http://localhost:$HGPORT/push-race
  1:67c9543981c6: initial - add source-file0 and source-file1
  2:eaf64eb11964: add dir0/file0
  executing: hg push -r eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 http://localhost:$HGPORT/push-race
  hg> pushing to http://localhost:$HGPORT/push-race
  hg> searching for changes
  hg> remote has heads on branch 'default' that are not known locally: 9482a15d6fcd
  hg> abort: push creates new remote head eaf64eb11964!
  hg> (pull and merge or see 'hg help push' for details about pushing new heads)
  likely push race on attempt 1/3
  retrying immediately...
  executing: hg strip --no-backup -r 'not public()'
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  pushing 2 new changesets on head eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 to http://localhost:$HGPORT/push-race
  1:67c9543981c6: initial - add source-file0 and source-file1
  2:eaf64eb11964: add dir0/file0
  executing: hg push -r eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 http://localhost:$HGPORT/push-race
  hg> pushing to http://localhost:$HGPORT/push-race
  hg> searching for changes
  hg> remote has heads on branch 'default' that are not known locally: 9482a15d6fcd
  hg> abort: push creates new remote head eaf64eb11964!
  hg> (pull and merge or see 'hg help push' for details about pushing new heads)
  likely push race on attempt 2/3
  retrying immediately...
  executing: hg strip --no-backup -r 'not public()'
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  pushing 2 new changesets on head eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 to http://localhost:$HGPORT/push-race
  1:67c9543981c6: initial - add source-file0 and source-file1
  2:eaf64eb11964: add dir0/file0
  executing: hg push -r eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 http://localhost:$HGPORT/push-race
  hg> pushing to http://localhost:$HGPORT/push-race
  hg> searching for changes
  hg> remote has heads on branch 'default' that are not known locally: 9482a15d6fcd
  hg> abort: push creates new remote head eaf64eb11964!
  hg> (pull and merge or see 'hg help push' for details about pushing new heads)
  likely push race on attempt 3/3
  overlay not successful after 3 attempts; try again later
  [1]

