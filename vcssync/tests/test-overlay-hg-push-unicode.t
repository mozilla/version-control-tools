#require hg40+

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

Test unicode in commit descriptions

  $ cd server/overlay-source
  $ echo 1 > file2
  $ hg commit --encoding utf-8 -A -m 'add file2 with unicode テスト'
  adding file2
  $ cd ../..

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir --result-push-url http://localhost:$HGPORT/overlay-dest
  repo does not exist; cloning http://localhost:$HGPORT/overlay-dest
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/repo/.hg/localhost~3a*__overlay-source (glob)
  hg> requesting all changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 3 changesets with 4 changes to 4 files
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  hg> 2943afe809e4 -> 45ba9d247354: add file2 with unicode \xe3\x83\x86\xe3\x82\xb9\xe3\x83\x88 (esc)
  3 new changesets; new tip is 45ba9d247354df64fa1811413f28f043ba6b7cdf
  pushing 3 new changesets on head 45ba9d247354df64fa1811413f28f043ba6b7cdf to http://localhost:$HGPORT/overlay-dest
  1:67c9543981c6: initial - add source-file0 and source-file1
  2:eaf64eb11964: add dir0/file0
  3:45ba9d247354: add file2 with unicode \xe3\x83\x86\xe3\x82\xb9\xe3\x83\x88 (esc)
  executing: hg push -r 45ba9d247354df64fa1811413f28f043ba6b7cdf http://localhost:$HGPORT/overlay-dest
  hg> pushing to http://localhost:$HGPORT/overlay-dest
  hg> searching for changes
  hg> remote: adding changesets
  hg> remote: adding manifests
  hg> remote: adding file changes
  hg> remote: added 3 changesets with 4 changes to 4 files

