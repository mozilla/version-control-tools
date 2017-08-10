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
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at wdirlock
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

Simulate a held lock on the working directory for a no-op pull but working
directory update.

  $ hg -R wdirlock acquirewlock
  $ readlink wdirlock/.hg/wlock
  dummyhost:* (glob)

  $ hg --config ui.timeout=1 robustcheckout http://localhost:$HGPORT/repo0 wdirlock --revision aada1b3e573f
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at wdirlock
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  waiting for lock on working directory of wdirlock held by * (glob)
  abort: working directory of wdirlock: timed out waiting for lock held by * (glob)
  [255]

Simulate a held lock on the working directory for a store pull and working
directory update.

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 wdirlock-pull --revision 5d6cdc75a09b
  ensuring http://localhost:$HGPORT/repo0@5d6cdc75a09b is available at wdirlock-pull
  updated to 5d6cdc75a09bcccf76f9339a28e1d89360c59dce

  $ cd server/repo0
  $ touch newfile
  $ hg -q commit -A -m 'add newfile'
  $ cd ../..

  $ hg -R wdirlock-pull acquirewlock
  $ readlink wdirlock-pull/.hg/wlock
  dummyhost:* (glob)

  $ hg --config ui.timeout=1 robustcheckout http://localhost:$HGPORT/repo0 wdirlock-pull --revision a7c4155bc8eb
  ensuring http://localhost:$HGPORT/repo0@a7c4155bc8eb is available at wdirlock-pull
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (pulling to obtain a7c4155bc8eb)
  waiting for lock on working directory of wdirlock-pull held by * (glob)
  abort: working directory of wdirlock-pull: timed out waiting for lock held by * (glob)
  [255]

Simulate a held lock on the store for a no-op pull and working directory
update. This should work because no store update is needed so no lock needs
to be acquired.

  $ hg -q robustcheckout http://localhost:$HGPORT/repo1 storelock --revision 7d5b54cb09e1
  ensuring http://localhost:$HGPORT/repo1@7d5b54cb09e1 is available at storelock
  updated to 7d5b54cb09e1172a3684402520112cab3f3a1b70
  $ hg -R storelock acquirestorelock
  $ readlink share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg/store/lock
  dummyhost:* (glob)

  $ hg --config ui.timeout=1 robustcheckout http://localhost:$HGPORT/repo1 storelock --revision 65cd4e3b46a3
  ensuring http://localhost:$HGPORT/repo1@65cd4e3b46a3 is available at storelock
  (existing repository shared store: $TESTTMP/share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 65cd4e3b46a3f22a08ec4162871e67f57c322f6a

Clean up for next test

  $ rm -rf share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a

Simulate a held lock on the store for a pull plus working directory update.

  $ hg -q robustcheckout http://localhost:$HGPORT/repo1 storelock-pull --revision 7d5b54cb09e1
  ensuring http://localhost:$HGPORT/repo1@7d5b54cb09e1 is available at storelock-pull
  updated to 7d5b54cb09e1172a3684402520112cab3f3a1b70
  $ hg -R storelock-pull acquirestorelock
  $ readlink share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg/store/lock
  dummyhost:* (glob)

  $ cd server/repo1
  $ touch newfile
  $ hg -q commit -A -m 'add newfile'
  $ cd ../..

  $ hg --config ui.timeout=1 robustcheckout http://localhost:$HGPORT/repo1 storelock-pull --revision fca136d824da
  ensuring http://localhost:$HGPORT/repo1@fca136d824da is available at storelock-pull
  (existing repository shared store: $TESTTMP/share/65cd4e3b46a3f22a08ec4162871e67f57c322f6a/.hg)
  (pulling to obtain fca136d824da)
  waiting for lock on repository storelock-pull held by * (glob)
  abort: repository storelock-pull: timed out waiting for lock held by * (glob)
  [255]
