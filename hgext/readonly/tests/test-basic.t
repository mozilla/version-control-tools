Create test server

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
  > globalreasonfile = $TESTTMP/globalreason
  > EOF

  $ hg serve -d -p $HGPORT --pid-file hg.pid -E error.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

Push to repository without any readonly reason files will work

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files

Empty local reason file prints generic message

  $ touch ../server/.hg/readonlyreason
  $ echo readonly > foo
  $ hg commit -m readonly
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: repository is read only
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]

Pushing a bookmark fails

  $ hg bookmark -r 0 bm0
  $ hg push -B bm0
  pushing to http://localhost:$HGPORT/
  searching for changes
  no changes found
  remote: repository is read only
  remote: refusing to update bookmarks
  remote: pushkey-abort: prepushkey.readonly hook failed
  abort: exporting bookmark bm0 failed!
  [255]

Local reason file with content prints message

  $ cat > ../server/.hg/readonlyreason << EOF
  > repository is no longer active
  > EOF

  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: repository is read only
  remote: repository is no longer active
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]

Global and local reason file should print local reason

  $ touch $TESTTMP/globalreason
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: repository is read only
  remote: repository is no longer active
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]

Global reason file in isolation works

  $ rm -f ../server/.hg/readonlyreason
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: all repositories currently read only
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]

Global reason file reason is printed

  $ cat > $TESTTMP/globalreason << EOF
  > this is the global reason
  > EOF

  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: all repositories currently read only
  remote: this is the global reason
  remote: refusing to add changesets
  remote: prechangegroup.readonly hook failed
  abort: push failed on remote
  [255]
