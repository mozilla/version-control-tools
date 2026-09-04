  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Set up a repository whose remote only ever exposes the initial commit. The
wanted revision is created in a separate, unserved clone and packaged as a
bundle, mimicking a decision-task artifact that carries the changesets between
a CDN clone bundle and the wanted revision.

  $ hg init server/repo-bundle
  $ cd server/repo-bundle
  $ touch foo
  $ hg -q commit -A -m initial
  $ cd ../..

  $ hg -q clone server/repo-bundle scratch
  $ cd scratch
  $ echo 1 > foo
  $ hg -q commit -m 1
  $ hg -q bundle --base 0 -r 1 $TESTTMP/rev1.hg
  $ cd ..

The bundle carries the wanted revision only; its base is the (already cloned)
initial revision.

  $ hg debugbundle $TESTTMP/rev1.hg
  Stream params: {Compression: BZ}
  changegroup -- {nbchanges: 1, version: 02} (mandatory: True)
      a33779fdfc23063680fc31e9ff637dff6876d3d2
  cache:rev-branch-cache -- {} (mandatory: False)

Seed the shared store with the initial revision only. The remote never learns
about the wanted revision, so a later pull for it would fail.

  $ hg robustcheckout http://localhost:$HGPORT/repo-bundle dest --revision 96ee1d7354c4
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo-bundle@96ee1d7354c4 is available at dest
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  7 files to transfer, * of data (glob) (hg67 !)
  6 files to transfer, * of data (glob) (no-hg67 !)
  transferred .* in \d+\.\d+ seconds \(.*\) (re) (no-hg70 !)
  stream-cloned \d+ files / .* in \d+(\.\d+)? seconds \(.*\) (re) (hg70 !)
  searching for changes
  new changesets 96ee1d7354c4 (?)
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 96ee1d7354c4ad7372047672c36a1f561e3a6a4c

Applying a bundle that carries the wanted revision lets robustcheckout obtain
it locally and skip the pull from the remote entirely (note the absence of any
"pulling to obtain" line; the remote does not even have this revision).

  $ hg robustcheckout http://localhost:$HGPORT/repo-bundle dest --revision a33779fdfc23 --bundle $TESTTMP/rev1.hg
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo-bundle@a33779fdfc23 is available at dest
  (existing repository shared store: $TESTTMP/share/96ee1d7354c4ad7372047672c36a1f561e3a6a4c/.hg)
  (applying bundle $TESTTMP/rev1.hg)
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to a33779fdfc23063680fc31e9ff637dff6876d3d2

  $ cat dest/foo
  1

A bundle path that does not exist is a non-fatal warning; robustcheckout
proceeds as if no bundle had been passed. The wanted revision is already in the
store, so no pull is needed.

  $ hg robustcheckout http://localhost:$HGPORT/repo-bundle dest --revision a33779fdfc23 --bundle $TESTTMP/missing.hg
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo-bundle@a33779fdfc23 is available at dest
  (existing repository shared store: $TESTTMP/share/96ee1d7354c4ad7372047672c36a1f561e3a6a4c/.hg)
  (bundle $TESTTMP/missing.hg does not exist; skipping)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to a33779fdfc23063680fc31e9ff637dff6876d3d2

A bundle that cannot be applied (here, a corrupt file) is also a non-fatal
warning; robustcheckout falls back to its normal behavior.

  $ echo 'not a bundle' > $TESTTMP/corrupt.hg
  $ hg robustcheckout http://localhost:$HGPORT/repo-bundle dest --revision a33779fdfc23 --bundle $TESTTMP/corrupt.hg
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/repo-bundle@a33779fdfc23 is available at dest
  (existing repository shared store: $TESTTMP/share/96ee1d7354c4ad7372047672c36a1f561e3a6a4c/.hg)
  (applying bundle $TESTTMP/corrupt.hg)
  (could not apply bundle $TESTTMP/corrupt.hg: *; falling back to pull) (glob)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to a33779fdfc23063680fc31e9ff637dff6876d3d2

Confirm no errors in log

  $ cat ./server/error.log
