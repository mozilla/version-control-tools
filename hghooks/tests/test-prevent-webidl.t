  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.prevent_webidl = python:mozhghooks.prevent_webidl_changes.hook
  > EOF

  $ echo "interface Foo{};" > original.webidl
  $ echo "foo" > dummy
  $ hg commit -A -m 'original repo commit; r=jst'
  adding dummy
  adding original.webidl

  $ cd ..
  $ hg clone server client
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
mq provides `hg strip` for older Mercurial versions and supplies it even
in modern versions
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mq=
  > EOF

Editing a .webidl file without any review should fail

  $ echo "interface Bar{};" >> original.webidl
  $ hg commit -m 'Bug 123 - Add Bar'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  
  WebIDL file original.webidl altered in changeset 35f6fa5728fb without DOM peer review
  
  
  Changes to WebIDL files in this repo require review from a DOM peer in the form of r=...
  This is to ensure that we behave responsibly with exposing new Web APIs. We appreciate your understanding..
  
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_webidl hook failed
  [255]

Editing a .webidl file without /DOM/ peer review should fail

  $ hg commit --amend -m 'Bug 123 - Add Bar; r=foobar'
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/35f6fa5728fb-amend-backup.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  
  ************************** ERROR ****************************
  
  WebIDL file original.webidl altered in changeset 17ac6dbbb5f7 without DOM peer review
  
  
  Changes to WebIDL files in this repo require review from a DOM peer in the form of r=...
  This is to ensure that we behave responsibly with exposing new Web APIs. We appreciate your understanding..
  
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_webidl hook failed
  [255]

Editing a .webidl file by DOM peers without review should pass

  $ hg commit --amend -u 'Johnny Stenback <jst@mozilla.com>' -m 'Bug 123 - Add Bar'
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/17ac6dbbb5f7-amend-backup.hg (glob)
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  You've received proper review from a DOM peer on your WebIDL change(s) in your push, thanks for paying enough attention.

Editing a .webidl file without proper DOM peer review when doing code uplift should pass

  $ echo "interface Uplift1{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar'
  $ echo "uplift1" > dummy
  $ hg commit -m 'Doing code upload; a=release'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files

WebIDL change after release uplift fails

  $ echo "uplift2" > dummy
  $ hg commit -m 'Doing the code uplift; a=release'
  $ echo "interface Uplift2{};" >> original.webidl
  $ hg commit -m 'Bug 12345; r=foobar'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  
  
  ************************** ERROR ****************************
  
  WebIDL file original.webidl altered in changeset b2b314a9c9d9 without DOM peer review
  
  
  Changes to WebIDL files in this repo require review from a DOM peer in the form of r=...
  This is to ensure that we behave responsibly with exposing new Web APIs. We appreciate your understanding..
  
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.prevent_webidl hook failed
  [255]

  $ hg strip -r 'draft()' > /dev/null

Multiple reviewers, one of which is a DOM peer, should be allowed

  $ echo "interface MultipleReviewers1{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar,jst'
  $ echo "interface MultipleReviewers2{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar r=jst'
  $ echo "interface MultipleReviewers3{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar r=lumpy,jst'
  $ echo "interface MultipleReviewers4{};" >> original.webidl
  $ hg commit -m 'Bug 123; sr=foobar,jst'
  $ echo "interface MultipleReviewers5{};" >> original.webidl
  $ hg commit -m 'Bug 123; sr=foobar sr=jst'
  $ echo "interface MultipleReviewers6{};" >> original.webidl
  $ hg commit -m 'Bug 123; sr=foobar sr=lumpy,jst'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 6 changesets with 6 changes to 1 files
  You've received proper review from a DOM peer on your WebIDL change(s) in your push, thanks for paying enough attention.

A merge commit touching a .webidl file with proper DOM peer review is allowed

  $ echo "interface Merge{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar,jst'
  $ mergerev=`hg log --template {rev} -r .`
  $ hg up -r 'last(public())'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo "merge" > dummy
  $ hg commit -m 'create a head'
  created new head
  $ hg merge $mergerev
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg commit -m 'merge'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 2 changes to 2 files
  You've received proper review from a DOM peer on your WebIDL change(s) in your push, thanks for paying enough attention.

Editing a .webidl file in a backout without proper DOM peer review is allowed

  $ echo "interface Test{};" > backout1.webidl
  $ hg commit -A -m 'Backed out changeset 593d94e9492e'
  adding backout1.webidl
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo "interface Test{};" > backout2.webidl
  $ hg commit -A -m 'Backout changesets 9e4ab3907b29, 3abc0dbbf710 due to m-oth permaorange'
  adding backout2.webidl
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo "interface Test{};" > backout3.webidl
  $ hg commit -A -m 'Backout of 35a679df430b due to bustage'
  adding backout3.webidl
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo "interface Test{};" > backout4.webidl
  $ hg commit -A -m 'backout 68941:5b8ade677818'
  adding backout4.webidl
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo "interface Test{};" > backout5.webidl
  $ hg commit -A -m 'Revert to changeset a87ee7550f6a due to incomplete backout'
  adding backout5.webidl
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo "interface Test{};" > backout6.webidl
  $ hg commit -A -m 'Backed out 7 changesets (bug 824717) for bustage.'
  adding backout6.webidl
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ cd ..

Hook should not run when stripping

  $ hg init striptest
  $ cd striptest
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ echo 'interface Bar{};' > original.webidl
  $ hg -q commit -A -m 'Add original.idl; r=jst'
  $ hg -q up -r 0
  $ echo 'interface Foo{};' > original.webidl
  $ hg -q commit -A -m 'Bad commit'
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > strip =
  > 
  > [hooks]
  > pretxnchangegroup.prevent_webidl = python:mozhghooks.prevent_webidl_changes.hook
  > EOF

  $ hg strip -r 1 --no-backup

  $ hg log -T '{rev} {desc}\n'
  1 Bad commit
  0 initial
