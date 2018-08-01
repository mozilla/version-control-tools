  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Add some files to server repo to test sparseness

  $ cd server/repo0
  $ hg -q up default
  $ mkdir dir0 dir1
  $ touch dir0/foo.c dir0/foo.h dir0/foo.py dir1/foo.py dir1/bar.py
  $ hg -q commit -A -m 'add some files to test sparse'
  $ mkdir profiles
  $ cat > profiles/python << EOF
  > [include]
  > glob:**/*.py
  > EOF
  $ cat > profiles/dir0 << EOF
  > [include]
  > glob:dir0/**
  > EOF
  $ cat > profiles/dir1 << EOF
  > [include]
  > glob:dir1/**
  > EOF
  $ hg -q commit -A -m 'add sparse profiles'
  $ touch dir1/baz.py
  $ hg -q commit -A -m 'add dir1/baz.py'
  $ cd ../..

#if no-hg43

  $ hg robustcheckout http://localhost:$HGPORT/repo0 dest --revision 5d6cdc75a09b --sparseprofile foo
  abort: sparse profile support only available for Mercurial versions greater than 4.3 (using *) (glob)
  [255]

#endif

#if hg43

Attempting a sparse checkout without sparse extension results in error

  $ hg robustcheckout http://localhost:$HGPORT/repo0 no-ext --revision 6af47298a235 --sparseprofile irrelevant
  abort: sparse extension must be enabled to use --sparseprofile
  [255]

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > sparse=
  > EOF

Enabling a sparse profile on a repo not using sparse is an error

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 no-sparse --revision 6af47298a235
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at no-sparse
  updated to 6af47298a235491213679cd4f91881d22c735c72

  $ hg robustcheckout http://localhost:$HGPORT/repo0 no-sparse --revision 6af47298a235 --sparseprofile irrelevant
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at no-sparse
  abort: cannot enable sparse profile on existing non-sparse checkout
  (use a separate working directory to use sparse)
  [255]

Specifying a sparse profile that doesn't exist results in error

  $ hg robustcheckout http://localhost:$HGPORT/repo0 bad-profile --revision 6af47298a235 --sparseprofile doesnotexist
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at bad-profile
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  no changes found
  abort: sparse profile doesnotexist does not exist at revision 6af47298a235491213679cd4f91881d22c735c72
  [255]

Specifying a sparse profile uses it

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-simple --revision 6af47298a235 --sparseprofile profiles/python
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at sparse-simple
  (sharing from existing pooled repository b8b78f0253d822e33ba652fd3d80a5c0837cfdf3)
  searching for changes
  no changes found
  (setting sparse config to profile profiles/python)
  0 files added, 0 files dropped, 0 files conflicting
  (sparse refresh complete)
  warning: sparse profile 'profiles/python' not found in rev 000000000000 - ignoring it
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 6af47298a235491213679cd4f91881d22c735c72

  $ hg -R sparse-simple files
  sparse-simple/dir0/foo.py
  sparse-simple/dir1/bar.py
  sparse-simple/dir1/foo.py

No-op update does something reasonable

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-simple --revision 6af47298a235 --sparseprofile profiles/python
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at sparse-simple
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (sparse profile profiles/python already set; no need to update sparse config)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 6af47298a235491213679cd4f91881d22c735c72

Attempting to remove sparse from a sparse checkout is not allowed

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-simple --revision 4916c5373fd6
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@4916c5373fd6 is available at sparse-simple
  abort: cannot use non-sparse checkout on existing sparse checkout
  (use a separate working directory to use sparse)
  [255]

Specifying a new sparse profile will replace existing profile

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-simple --revision 6af47298a235 --sparseprofile profiles/dir0
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at sparse-simple
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (replacing existing sparse config with profile profiles/dir0)
  2 files added, 2 files dropped, 0 files conflicting
  (sparse refresh complete)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 6af47298a235491213679cd4f91881d22c735c72

  $ hg -R sparse-simple files
  sparse-simple/dir0/foo.c
  sparse-simple/dir0/foo.h
  sparse-simple/dir0/foo.py

Specifying a new sparse profile and updating the revision works

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-simple --revision 4916c5373fd6 --sparseprofile profiles/dir1
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@4916c5373fd6 is available at sparse-simple
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (replacing existing sparse config with profile profiles/dir1)
  2 files added, 3 files dropped, 0 files conflicting
  (sparse refresh complete)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 4916c5373fd67aca0412e74b0ffeeb0291a86bfd

  $ hg -R sparse-simple files
  sparse-simple/dir1/bar.py
  sparse-simple/dir1/baz.py
  sparse-simple/dir1/foo.py

Purging a file outside the sparse profile works

  $ hg -q robustcheckout http://localhost:$HGPORT/repo0 sparse-purge --revision 6af47298a235 --sparseprofile profiles/dir0
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at sparse-purge
  (setting sparse config to profile profiles/dir0)
  (sparse refresh complete)
  warning: sparse profile 'profiles/dir0' not found in rev 000000000000 - ignoring it
  updated to 6af47298a235491213679cd4f91881d22c735c72

Purging with update to same revision

  $ mkdir sparse-purge/dir1 sparse-purge/dir2
  $ touch sparse-purge/dir0/extrafile sparse-purge/dir1/extrafile sparse-purge/dir2/extrafile

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-purge --revision 6af47298a235 --sparseprofile profiles/dir0 --purge
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at sparse-purge
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (purging working directory)
  (sparse profile profiles/dir0 already set; no need to update sparse config)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 6af47298a235491213679cd4f91881d22c735c72

  $ find sparse-purge -type f -name extrafile
  $ hg --cwd sparse-purge status --all
  C dir0/foo.c
  C dir0/foo.h
  C dir0/foo.py

Purging with update to different revision

  $ mkdir sparse-purge/dir1 sparse-purge/dir2
  $ touch sparse-purge/dir0/extrafile sparse-purge/dir1/extrafile sparse-purge/dir2/extrafile

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-purge --revision 4916c5373fd6 --sparseprofile profiles/dir0 --purge
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@4916c5373fd6 is available at sparse-purge
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (purging working directory)
  (sparse profile profiles/dir0 already set; no need to update sparse config)
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 4916c5373fd67aca0412e74b0ffeeb0291a86bfd

  $ find sparse-purge -type f -name extrafile
  $ hg --cwd sparse-purge status --all
  C dir0/foo.c
  C dir0/foo.h
  C dir0/foo.py

Purge with update to different revision and profile

  $ mkdir sparse-purge/dir1 sparse-purge/dir2
  $ touch sparse-purge/dir0/extrafile sparse-purge/dir1/extrafile sparse-purge/dir2/extrafile

  $ hg robustcheckout http://localhost:$HGPORT/repo0 sparse-purge --revision 6af47298a235 --sparseprofile profiles/dir1 --purge
  (using Mercurial *) (glob)
  ensuring http://localhost:$HGPORT/repo0@6af47298a235 is available at sparse-purge
  (existing repository shared store: $TESTTMP/share/b8b78f0253d822e33ba652fd3d80a5c0837cfdf3/.hg)
  (purging working directory)
  (replacing existing sparse config with profile profiles/dir1)
  3 files added, 3 files dropped, 0 files conflicting
  (sparse refresh complete)
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to 6af47298a235491213679cd4f91881d22c735c72

  $ find sparse-purge -type f -name extrafile
  $ hg --cwd sparse-purge status --all
  C dir1/bar.py
  C dir1/foo.py

#endif

Confirm no errors in log

  $ cat ./server/error.log
