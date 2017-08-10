  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Checking out to an existing repo that isn't shared will blow it away

  $ hg init dest0
  $ touch dest0/file0

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest0 --revision aada1b3e573f
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at dest0
  (destination is not shared; deleting)
  (sharing from new pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

  $ ls dest0
  foo

If shared path points nowhere, repo is "corrupt"; should be blown away

  $ hg share -U dest0 missingsharepath
  $ cat > missingsharepath/.hg/sharedpath << EOF
  > does_not_exist
  > EOF
  $ touch missingsharepath/file0

  $ hg robustcheckout http://localhost:$HGPORT/repo0 missingsharepath --revision aada1b3e573f
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at missingsharepath
  (existing repository shared store: does_not_exist)
  (shared store does not exist; deleting destination)
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

  $ ls missingsharepath
  foo

  $ cat missingsharepath/.hg/sharedpath
  $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg (no-eol)

If shared path does not point to pooled storage, it should get nuked as
we require pooled storage

  $ hg share -U dest0 nopoolshare
  $ hg init fakeshare
  $ cat > nopoolshare/.hg/sharedpath << EOF
  > $TESTTMP/fakeshare/.hg
  > EOF

  $ touch nopoolshare/file0
  $ hg robustcheckout http://localhost:$HGPORT/repo0 nopoolshare --revision aada1b3e573f
  ensuring http://localhost:$HGPORT/repo0@aada1b3e573f is available at nopoolshare
  (existing repository shared store: $TESTTMP/fakeshare/.hg)
  (shared store does not belong to pooled storage; deleting destination to improve efficiency)
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to aada1b3e573f7272bb2ef93b34acbf0f77c69d44

  $ ls nopoolshare
  foo
