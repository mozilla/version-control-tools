  $ . $TESTDIR/hghooks/tests/common.sh

Commit adding an FTL file without appropriate reviewer errors

  $ hg init normal
  $ configurehooks normal
  $ touch normal/.hg/IS_FIREFOX_REPO
  $ hg -q clone normal client-normal
  $ cd client-normal
  $ touch test.ftl
  $ hg -q commit -A -m 'add test.ftl'
  $ hg push
  pushing to $TESTTMP/normal
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  ************************ ERROR *************************
  You are trying to commit a change to an FTL file.
  At the moment modifying FTL files requires a review from
  one of the L10n Drivers.
  Please, request review from either:
      - Francesco Lodolo (:flod)
      - Zibi Braniecki (:gandalf)
      - Axel Hecht (:pike)
      - Stas Malolepszy (:stas)
  ********************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Commit adding an FTL file with appropriate reviewer works

  $ hg commit --amend -m 'add test.ftl. r=flod'
  saved backup bundle to $TESTTMP/client-normal/.hg/strip-backup/caf1d529f784-2085d403-amend*.hg (glob)
  $ hg push
  pushing to $TESTTMP/normal
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Commit adding an FTL file with appropriate reviewer works

  $ touch test2.ftl
  $ hg -q commit -A -m 'add test2.ftl. r=someonelse,stas'
  $ hg push
  pushing to $TESTTMP/normal
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Commit adding an FTL file with appropriate reviewer works, case-independent

  $ touch test3.ftl
  $ hg -q commit -A -m 'add test3.ftl. r=Pike'
  $ hg push
  pushing to $TESTTMP/normal
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
