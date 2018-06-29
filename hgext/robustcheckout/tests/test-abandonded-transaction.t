  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at dest
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets b8b78f0253d8:aada1b3e573f (?)
  searching for changes
  no changes found
  devel-warn: changectx.__init__ is getting more limited, see context.changectxdeprecwarn() for details (hg46 !)
  (compatibility will be dropped after Mercurial-4.6, update your code.) at: */mercurial/localrepo.py:849 (__contains__) (glob) (hg46 !)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ hg -R dest --config extensions.strip= strip -r aada1b3e573f --no-backup

Simulate an abandonded transaction

  $ touch $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/store/journal

Pulling when there is an abandoned transaction should automatically recover

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision aada1b3e573f
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain aada1b3e573f)
  searching for changes
  (abandoned transaction found; trying to recover)
  rolling back interrupted transaction
  (attempting checkout from beginning)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain aada1b3e573f)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  new changesets aada1b3e573f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

Now simulate an abandoned transaction on an initial checkout

  $ hg -R dest --config extensions.strip= strip -r aada1b3e573f --no-backup
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ touch $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg/store/journal

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest2 --revision aada1b3e573f
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest2
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  (abandoned transaction found; trying to recover)
  rolling back interrupted transaction
  (attempting checkout from beginning)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest2
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain aada1b3e573f)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  new changesets aada1b3e573f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

Confirm no errors in log

  $ cat ./server/error.log
