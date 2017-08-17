  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

  $ cat > testlock.py << EOF
  > from mercurial import cmdutil, commands, lock as lockmod, registrar, util
  > cmdtable = {}
  > if util.safehasattr(registrar, 'command'):
  >     command = registrar.command(cmdtable)
  > else:
  >     command = cmdutil.command(cmdtable)
  > @command('acquirewlock')
  > def acquirewlock(ui, repo):
  >     lockmod.lock._host = 'dummyhost'
  >     wlock = repo.wlock()
  >     setattr(wlock, 'release', lambda: None)
  > @command('acquirestorelock')
  > def acquirestorelock(ui, repo):
  >     lockmod.lock._host = 'dummyhost'
  >     wlock = repo.wlock()
  >     lock = repo.lock()
  >     setattr(lock, 'release', lambda: None)
  > EOF

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > testlock = $TESTTMP/testlock.py
  > EOF

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 wdirlock --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at wdirlock
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Simulate a held lock on the working directory for a no-op pull but working
directory update.

  $ hg -R wdirlock acquirewlock
  $ readlink wdirlock/.hg/wlock
  dummyhost:* (glob)

  $ hg robustcheckout http://localhost:$HGPORT/repo0 wdirlock --revision aada1b3e573f
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at wdirlock
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (dest has an active working directory lock; assuming it is left over from a previous process and that the destination is corrupt; deleting it just to be sure)
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

Simulate a held lock on the working directory for a store pull and working
directory update.

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 wdirlock-pull --revision 5d6cdc75a09b
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at wdirlock-pull
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cd server/repo0
  $ touch newfile
  $ hg -q commit -A -m 'add newfile'
  $ cd ../..

  $ hg -R wdirlock-pull acquirewlock
  $ readlink wdirlock-pull/.hg/wlock
  dummyhost:* (glob)

  $ hg robustcheckout http://localhost:$HGPORT/repo0 wdirlock-pull --revision a7c4155bc8eb
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@a7c4155bc8eb is available at wdirlock-pull
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (dest has an active working directory lock; assuming it is left over from a previous process and that the destination is corrupt; deleting it just to be sure)
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to a7c4155bc8eb86ecec78c91f744f597e7c9a3ff3

Simulate a held lock on the store for a no-op pull and working directory
update. This should work because no store update is needed so no lock needs
to be acquired.

  $ hg -q robustcheckout http://localhost:$HGPORT/repo1 storelock --revision 7d5b54cb09e1
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo1@7d5b54cb09e1 is available at storelock
  updated to 7d5b54cb09e1172a3684402520112cab3f3a1b70
  $ hg -R storelock acquirestorelock
  $ readlink share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg/store/lock
  dummyhost:* (glob)

  $ hg robustcheckout http://localhost:$HGPORT/repo1 storelock --revision 65cd4e3b46a3
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo1@65cd4e3b46a3 is available at storelock
  (existing repository shared store: $TESTTMP/share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg)
  (shared store has an active lock; assuming it is left over from a previous process and that the store is corrupt; deleting store and destination just to be sure)
  (sharing from new pooled repository 65cd4e3b46a3f22a08ec4162871e67f57c322f6a)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 65cd4e3b46a3f22a08ec4162871e67f57c322f6a

Clean up for next test

  $ rm -rf share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a

Simulate a held lock on the store for a pull plus working directory update.

  $ hg -q robustcheckout http://localhost:$HGPORT/repo1 storelock-pull --revision 7d5b54cb09e1
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo1@7d5b54cb09e1 is available at storelock-pull
  updated to 7d5b54cb09e1172a3684402520112cab3f3a1b70
  $ hg -R storelock-pull acquirestorelock
  $ readlink share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg/store/lock
  dummyhost:* (glob)

  $ cd server/repo1
  $ touch newfile
  $ hg -q commit -A -m 'add newfile'
  $ cd ../..

  $ hg robustcheckout http://localhost:$HGPORT/repo1 storelock-pull --revision fca136d824da
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo1@fca136d824da is available at storelock-pull
  (existing repository shared store: $TESTTMP/share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg)
  (shared store has an active lock; assuming it is left over from a previous process and that the store is corrupt; deleting store and destination just to be sure)
  (sharing from new pooled repository 65cd4e3b46a3f22a08ec4162871e67f57c322f6a)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 2 files
  searching for changes
  no changes found
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to fca136d824dac41b19345549edfda68fe63213c4

Simulate a held lock on the store without a working directory

  $ hg -R storelock acquirestorelock
  $ readlink share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg/store/lock
  dummyhost:* (glob)

  $ hg robustcheckout http://localhost:$HGPORT/repo1 storelock-nowdir --revision 7d5b54cb09e1
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo1@7d5b54cb09e1 is available at storelock-nowdir
  (shared store has an active lock; assuming it is left over from a previous process and that the store is corrupt; deleting store and destination just to be sure)
  (sharing from new pooled repository 65cd4e3b46a3f22a08ec4162871e67f57c322f6a)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 2 files
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 7d5b54cb09e1172a3684402520112cab3f3a1b70
