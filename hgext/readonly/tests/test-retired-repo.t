Create a retired test server

  $ hg init server
  $ cd server
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > readonly = $TESTDIR/hgext/readonly
  > 
  > [web]
  > push_ssl = false
  > allow_push = *
  > 
  > [readonly]
  > retiredurl = https://github.com/mozilla/nspr
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial

  $ hg serve -d -p $HGPORT --pid-file hg.pid -E error.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

A retired repository can still be cloned

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ hg log -T '{desc}\n'
  initial

Pushing to a retired repository points at the new location

  $ echo retired > foo
  $ hg commit -m retired
  $ hg push
  pushing to http://$LOCALHOST:$HGPORT/
  searching for changes
  remote: repository is retired and read only
  remote: the code in this repository now lives at https://github.com/mozilla/nspr
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]

Pushing a bookmark to a retired repository fails

  $ hg bookmark -r 0 bm0
  $ hg push -B bm0
  pushing to http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found
  remote: repository is retired and read only
  remote: the code in this repository now lives at https://github.com/mozilla/nspr
  remote: refusing to update bookmarks
  remote: prepushkey.readonly hook failed
  abort: push failed on remote
  [255]

Confirm no errors in log

  $ cat ../server/error.log
