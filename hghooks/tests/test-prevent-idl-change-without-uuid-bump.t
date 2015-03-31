#require hg32+
  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.prevent_idl_change_without_uuid_bump = python:mozhghooks.prevent_idl_change_without_uuid_bump.hook
  > EOF

Initing repo should work.

  $ hg init client
  $ cd client

Adding and modifying non-IDL files should work.

  $ cat > a.txt << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  > };
  > EOF

  $ hg commit -A -m 'a.txt'
  adding a.txt

  $ cat > a.txt << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  >   void test();
  > };
  > EOF

  $ hg commit -A -m 'a.txt'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files

Adding a new IDL file should work.

  $ cat > a.idl << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  adding a.idl

  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Modifying interface should fail.

  $ cat > a.idl << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  >   void test();
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  *************************** ERROR ***************************
  Push rejected because the following IDL interfaces were
  modified without changing the UUID:
    - A in changeset d37488062eb5
  
  To update the UUID for all of the above interfaces and their
  descendants, run:
    ./mach update-uuids A
  
  If you intentionally want to keep the current UUID, include
  'IGNORE IDL' in the commit message.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_idl_change_without_uuid_bump hook failed
  [255]

Using 'IGNORE IDL' should work.

  $ hg commit --amend -m 'a.idl IGNORE IDL' >/dev/null
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Modifying interface in two separate commits should fail.

  $ cat > a.idl << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  $ cat > a.idl << EOF
  > [scriptable, uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  
  *************************** ERROR ***************************
  Push rejected because the following IDL interfaces were
  modified without changing the UUID:
    - A in changeset 6166c7b45675
    - A in changeset d275ef228c2c
  
  To update the UUID for all of the above interfaces and their
  descendants, run:
    ./mach update-uuids A
  
  If you intentionally want to keep the current UUID, include
  'IGNORE IDL' in the commit message.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_idl_change_without_uuid_bump hook failed
  [255]

Using 'a=release' in tip commit should work.

  $ hg commit --amend -m 'a.idl a=release' >/dev/null
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files

Modifying interface should work if UUID is changed.

  $ cat > a.idl << EOF
  > [uuid(395fe045-7d18-4adb-a3fd-af98c8a1af11)]
  > interface A {
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Adding a new interface should work.

  $ cat >> a.idl << EOF
  > [uuid(204555e7-04ad-4cc8-9f0e-840615cc43e8)]
  > interface A2 {
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Modifying both interfaces file should fail.

  $ cat > a.idl << EOF
  > [uuid(395fe045-7d18-4adb-a3fd-af98c8a1af11)]
  > interface A {
  >   void test();
  > };
  > [scriptable, uuid(204555e7-04ad-4cc8-9f0e-840615cc43e8)]
  > interface A2 {
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  *************************** ERROR ***************************
  Push rejected because the following IDL interfaces were
  modified without changing the UUID:
    - A in changeset 8fa01e4e5a1d
    - A2 in changeset 8fa01e4e5a1d
  
  To update the UUID for all of the above interfaces and their
  descendants, run:
    ./mach update-uuids A A2
  
  If you intentionally want to keep the current UUID, include
  'IGNORE IDL' in the commit message.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_idl_change_without_uuid_bump hook failed
  [255]

Modifying both interfaces should fail even when one UUID is changed.

  $ cat > a.idl << EOF
  > [uuid(395fe045-7d18-4adb-a3fd-af98c8a1af11)]
  > interface A {
  >   void test();
  > };
  > [scriptable, uuid(1f341018-521a-49de-b806-1bef5c9a00b0)]
  > interface A2 {
  > };
  > EOF

  $ hg commit --amend -A >/dev/null
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  *************************** ERROR ***************************
  Push rejected because the following IDL interfaces were
  modified without changing the UUID:
    - A in changeset be234b691fe3
  
  To update the UUID for all of the above interfaces and their
  descendants, run:
    ./mach update-uuids A
  
  If you intentionally want to keep the current UUID, include
  'IGNORE IDL' in the commit message.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_idl_change_without_uuid_bump hook failed
  [255]

Modifying one interface and its UUID should work.

  $ cat > a.idl << EOF
  > [uuid(395fe045-7d18-4adb-a3fd-af98c8a1af11)]
  > interface A {
  > };
  > [scriptable, uuid(1f341018-521a-49de-b806-1bef5c9a00b0)]
  > interface A2 {
  > };
  > EOF

  $ hg commit --amend -A >/dev/null
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Removing one interface should work.

  $ cat > a.idl << EOF
  > [uuid(395fe045-7d18-4adb-a3fd-af98c8a1af11)]
  > interface A {
  > };
  > EOF

  $ hg commit -A -m 'a.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Copying an IDL file should work.

  $ hg cp a.idl acopy.idl
  $ hg commit -A -m 'acopy.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Moving an IDL file should work.

  $ hg mv acopy.idl amove.idl
  $ hg commit -A -m 'amove.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Deleting an IDL file should work.

  $ hg rm a.idl
  $ hg commit -A -m 'a.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files

Adding and modifying multiple IDL files should fail if UUID is not bumped.

  $ cat > a.idl << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  > };
  > EOF

  $ cat > b.idl << EOF
  > [uuid(1f341018-521a-49de-b806-1bef5c9a00b0)]
  > interface B {
  > };
  > EOF

  $ hg commit -A -m 'a.idl b.idl'
  adding a.idl
  adding b.idl

  $ cat > a.idl << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  >   void test();
  > };
  > EOF

  $ cat > b.idl << EOF
  > [uuid(1f341018-521a-49de-b806-1bef5c9a00b0)]
  > interface B : public A {
  > };
  > EOF

  $ hg commit -A -m 'a.idl b.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  
  *************************** ERROR ***************************
  Push rejected because the following IDL interfaces were
  modified without changing the UUID:
    - A in changeset a1f62287c4dd
    - B in changeset a1f62287c4dd
  
  To update the UUID for all of the above interfaces and their
  descendants, run:
    ./mach update-uuids A B
  
  If you intentionally want to keep the current UUID, include
  'IGNORE IDL' in the commit message.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_idl_change_without_uuid_bump hook failed
  [255]

Comments and changes outside interface blocks should be ignored.

  $ cat > a.idl << EOF
  > /* test */[uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {// foo
  >   void /* bar */test();// baz
  > };
  > EOF

  $ cat > b.idl << EOF
  > interface Foo;
  > /* test
  >  * test
  >  */
  > [uuid(1f341018-521a-49de-b806-1bef5c9a00b0)]
  > interface B {
  > };
  > test
  > EOF

  $ hg commit --amend -A >/dev/null
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 3 changes to 2 files

Adding and modifying an oddly formatted but still valid IDL should fail if
UUID is not bumped.

  $ cat > nsISupports.idl << EOF
  >  [ scriptable,
  >    uuid (
  >      00000000-0000-0000-c000-000000000046
  >    ), builtinclass
  >   ]
  >  interface    nsISupports    {
  >   };
  > EOF

  $ hg commit -A -m 'nsISupports.idl'
  adding nsISupports.idl

  $ cat > nsISupports.idl << EOF
  >  [ scriptable,
  >    uuid (
  >      00000000-0000-0000-c000-000000000046
  >    )
  >   ]
  >  interface    nsISupports    {
  >   };
  > EOF

  $ hg commit -A -m 'nsISupports.idl'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  
  *************************** ERROR ***************************
  Push rejected because the following IDL interfaces were
  modified without changing the UUID:
    - nsISupports in changeset c4abf967d1fe
  
  To update the UUID for all of the above interfaces and their
  descendants, run:
    ./mach update-uuids nsISupports
  
  If you intentionally want to keep the current UUID, include
  'IGNORE IDL' in the commit message.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_idl_change_without_uuid_bump hook failed
  [255]

  $ hg commit --amend -m 'nsISupports.idl IGNORE IDL'
  saved backup bundle to * (glob)

  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files

Merge commits should be ignored

  $ cat > a.idl << EOF
  > [uuid(00000000-0000-0000-c000-000000000046)]
  > interface A {
  > };
  > EOF

  $ hg commit -A -m 'a.idl IGNORE IDL'
  $ mergerev=`hg log --template {rev} -r .`
  $ hg up -r 'last(public())'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ echo 'merge' > dummy
  $ hg commit -A -m 'create a head'
  adding dummy
  created new head

  $ hg merge $mergerev
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)

  $ hg commit -m 'merge'
  $ hg push $TESTTMP/server
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 2 changes to 2 files

Stripping should not trigger hook

  $ cd ..
  $ hg init striptest
  $ cd striptest
  $ cat > original.idl << EOF
  > [uuid(00000000-0000-0000-0000-000000000001)]
  > interface nsIOriginal { };
  > EOF

  $ hg -q commit -A -m 'initial'
  $ cat > original.idl << EOF
  > [uuid(00000000-0000-0000-0000-000000000001)]
  > interface nsIOriginal { foo; };
  > EOF

  $ hg commit -m 'interface change, IGNORE IDL'
  $ hg -q up -r 0
  $ cat > original.idl << EOF
  > [uuid(00000000-0000-0000-0000-000000000001)]
  > interface nsIOriginal { bar; };
  > EOF

  $ hg commit -m 'bad interface change'
  created new head

  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > strip =
  > 
  > [hooks]
  > pretxnchangegroup.prevent_idl_change_without_uuid_bump = python:mozhghooks.prevent_idl_change_without_uuid_bump.hook
  > EOF

  $ hg strip -r 1 --no-backup
  $ hg log -T '{rev} {desc}\n'
  1 bad interface change
  0 initial
