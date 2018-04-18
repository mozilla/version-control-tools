
  $ . $TESTDIR/hghooks/tests/common.sh

  $ hg init server
  $ configurehooks server
  $ touch server/.hg/IS_FIREFOX_REPO
  $ cd server

  $ echo "interface Foo{};" > original.webidl
  $ echo "foo" > dummy
  $ hg commit -A -m 'original repo commit; r=baku'
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
  
  ******************************* ERROR *******************************
  Changeset 743ef64f8a38 alters WebIDL file(s) without DOM peer review:
  original.webidl
  
  Please, request review from either:
    - Andrea Marchesini (:baku)
    - Andrew McCreight (:mccr8)
    - Ben Kelly (:bkelly)
    - Blake Kaplan (:mrbkap)
    - Bobby Holley (:bholley)
    - Boris Zbarsky (:bz)
    - Ehsan Akhgari (:ehsan)
    - Henri Sivonen (:hsivonen)
    - Kyle Machulis (:qdot)
    - Nika Layzell (:mystor)
    - Olli Pettay (:smaug)
    - Peter Van der Beken (:peterv)
  *********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Editing a .webidl file without /DOM/ peer review should fail

  $ hg -q commit --amend -m 'Bug 123 - Add Bar; r=foobar'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  ******************************* ERROR *******************************
  Changeset 0cfb912b8138 alters WebIDL file(s) without DOM peer review:
  original.webidl
  
  Please, request review from either:
    - Andrea Marchesini (:baku)
    - Andrew McCreight (:mccr8)
    - Ben Kelly (:bkelly)
    - Blake Kaplan (:mrbkap)
    - Bobby Holley (:bholley)
    - Boris Zbarsky (:bz)
    - Ehsan Akhgari (:ehsan)
    - Henri Sivonen (:hsivonen)
    - Kyle Machulis (:qdot)
    - Nika Layzell (:mystor)
    - Olli Pettay (:smaug)
    - Peter Van der Beken (:peterv)
  *********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Editing a .webidl file by DOM peers without review should pass

  $ hg -q commit --amend -u 'Andrea Marchesini <amarchesini@mozilla.com>' -m 'Bug 123 - Add Bar'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Editing a .webidl file without /DOM/ peer review in the same push as a commit with review should fail

  $ echo "interface Update1{};" >> original.webidl
  $ hg -q commit -m 'Bug 123; r=baku'
  $ echo "interface Update2{};" >> original.webidl
  $ hg -q commit -m 'Bug 123'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  
  ******************************* ERROR *******************************
  Changeset a9b3d7778cda alters WebIDL file(s) without DOM peer review:
  original.webidl
  
  Please, request review from either:
    - Andrea Marchesini (:baku)
    - Andrew McCreight (:mccr8)
    - Ben Kelly (:bkelly)
    - Blake Kaplan (:mrbkap)
    - Bobby Holley (:bholley)
    - Boris Zbarsky (:bz)
    - Ehsan Akhgari (:ehsan)
    - Henri Sivonen (:hsivonen)
    - Kyle Machulis (:qdot)
    - Nika Layzell (:mystor)
    - Olli Pettay (:smaug)
    - Peter Van der Beken (:peterv)
  *********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

  $ hg -q strip '.^'

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
  
  ******************************* ERROR *******************************
  Changeset 3043c2c5e650 alters WebIDL file(s) without DOM peer review:
  original.webidl
  
  Please, request review from either:
    - Andrea Marchesini (:baku)
    - Andrew McCreight (:mccr8)
    - Ben Kelly (:bkelly)
    - Blake Kaplan (:mrbkap)
    - Bobby Holley (:bholley)
    - Boris Zbarsky (:bz)
    - Ehsan Akhgari (:ehsan)
    - Henri Sivonen (:hsivonen)
    - Kyle Machulis (:qdot)
    - Nika Layzell (:mystor)
    - Olli Pettay (:smaug)
    - Peter Van der Beken (:peterv)
  *********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

  $ hg strip -r 'draft()' > /dev/null

Multiple reviewers, one of which is a DOM peer, should be allowed

  $ echo "interface MultipleReviewers1{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar,baku'
  $ echo "interface MultipleReviewers2{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar r=baku'
  $ echo "interface MultipleReviewers3{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar r=lumpy,baku'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files

A merge commit touching a .webidl file with proper DOM peer review is allowed

  $ echo "interface Merge{};" >> original.webidl
  $ hg commit -m 'Bug 123; r=foobar,baku'
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
  $ hg -q commit -A -m 'Add original.idl; r=baku'
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

  $ cd ..

.webidl files in servo/ are immune from the hook

  $ cd client
  $ mkdir servo
  $ echo "interface Test{};" > servo/interface.webidl
  $ hg commit -A -m 'add interface in servo'
  adding servo/interface.webidl
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  -- Not enforcing DOM peer review for WebIDL files within Servo.
  -- Please make sure changes do not contain any web-visible binding definitions.

Editing a .webidl file that isn't in a web root should pass

  $ mkdir -p dom/chrome-webidl
  $ echo "[ChromeOnly] interface MozFoo{};" > dom/chrome-webidl/MozFoo.webidl
  $ hg add dom/chrome-webidl/MozFoo.webidl
  $ hg commit -m 'Bug 123 - Add MozFoo'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  -- Not enforcing DOM peer review for WebIDL files within the chrome WebIDL root.
  -- Please make sure changes do not contain any web-visible binding definitions.

Editing multiple .webidl files without review should fail

  $ echo "interface Foo{};" >> dom/file1.webidl
  $ echo "interface Bar{};" >> dom/file2.webidl
  $ hg commit -q -A -m 'Bug 123 - Add Foo and Bar'
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  
  ******************************* ERROR *******************************
  Changeset 4cc0a6ce2e87 alters WebIDL file(s) without DOM peer review:
  dom/file1.webidl
  dom/file2.webidl
  
  Please, request review from either:
    - Andrea Marchesini (:baku)
    - Andrew McCreight (:mccr8)
    - Ben Kelly (:bkelly)
    - Blake Kaplan (:mrbkap)
    - Bobby Holley (:bholley)
    - Boris Zbarsky (:bz)
    - Ehsan Akhgari (:ehsan)
    - Henri Sivonen (:hsivonen)
    - Kyle Machulis (:qdot)
    - Nika Layzell (:mystor)
    - Olli Pettay (:smaug)
    - Peter Van der Beken (:peterv)
  *********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
 
