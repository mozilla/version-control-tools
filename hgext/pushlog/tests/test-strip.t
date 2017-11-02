  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurepushlog server

  $ hg init client
  $ export USER=hguser

  $ cd client
  $ touch foo
  $ hg commit -A -m 'initial'
  adding foo
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog
  $ echo foo2 > foo
  $ hg commit -m 'second'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog

Stripping changesets should result in pushlog getting stripped

  $ cd ../server
  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 2; user: hguser; Date: \d+; Rev: 1; Node: d0fddd3a3fb51076c33010ecf66692621f989a2c (re)
  $ hg --config extensions.mq= strip -r 1 --no-backup
  changeset will be deleted from pushlog: d0fddd3a3fb51076c33010ecf66692621f989a2c

  $ hg log
  changeset:   0:96ee1d7354c4
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     initial
  
  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)

#if hg42
  $ cat .hg/blackbox.log
  * deleted 1 changesets from pushlog: d0fddd3a3fb51076c33010ecf66692621f989a2c (glob)
  * --config 'extensions.mq=' strip -r 1 --no-backup exited 0 after * (glob)
#else
  $ cat .hg/blackbox.log
  * deleted 1 changesets from pushlog: d0fddd3a3fb51076c33010ecf66692621f989a2c (glob)
  * --config extensions.mq= strip -r 1 --no-backup exited 0 after * (glob)
#endif

  $ rm .hg/blackbox.log

Now try a more complicated example with changesets in the push history
being stripped. This tests rev reordering in pushlog database

  $ cd ../client
  $ hg -q up -r 0

  $ echo c1 > foo
  $ hg commit -m 'head 1 commit 1'
  created new head
  $ echo c2 > foo
  $ hg commit -m 'head 1 commit 2'
  $ hg push -f -r . ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  recorded push in pushlog

  $ hg -q up -r 0
  $ echo c3 > foo
  $ hg commit -m 'head 2 commit 1'
  created new head
  $ echo c4 > foo
  $ hg commit -m 'head 2 commit 2'
  $ hg push -f -r . ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files (+1 heads)
  recorded push in pushlog

  $ cd ../server

  $ hg log -T '{rev} {node} {desc}\n'
  4 5ad35eee611812e38f944019076bd4ed6b095d97 head 2 commit 2
  3 8fda3d2bda784adb73caa3fdbefe2421407d49b7 head 2 commit 1
  2 919c29ac42c0b25851d19be2d9d3883c45ba2ce4 head 1 commit 2
  1 4ffc55273fa6240122db584d4c96bb9be4280e7d head 1 commit 1
  0 96ee1d7354c4ad7372047672c36a1f561e3a6a4c initial

  $ hg --config extensions.mq= strip -r 2 --no-backup
  changeset will be deleted from pushlog: 919c29ac42c0b25851d19be2d9d3883c45ba2ce4
  changeset rev will be updated in pushlog: 8fda3d2bda784adb73caa3fdbefe2421407d49b7
  changeset rev will be updated in pushlog: 5ad35eee611812e38f944019076bd4ed6b095d97

  $ hg log -T '{rev} {node} {desc}\n'
  3 5ad35eee611812e38f944019076bd4ed6b095d97 head 2 commit 2
  2 8fda3d2bda784adb73caa3fdbefe2421407d49b7 head 2 commit 1
  1 4ffc55273fa6240122db584d4c96bb9be4280e7d head 1 commit 1
  0 96ee1d7354c4ad7372047672c36a1f561e3a6a4c initial

Note the missing push ID 2!
  $ dumppushlog server
  ID: 1; user: hguser; Date: \d+; Rev: 0; Node: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c (re)
  ID: 3; user: hguser; Date: \d+; Rev: 1; Node: 4ffc55273fa6240122db584d4c96bb9be4280e7d (re)
  ID: 4; user: hguser; Date: \d+; Rev: 2; Node: 8fda3d2bda784adb73caa3fdbefe2421407d49b7 (re)
  ID: 4; user: hguser; Date: \d+; Rev: 3; Node: 5ad35eee611812e38f944019076bd4ed6b095d97 (re)

#if hg42
  $ cat .hg/blackbox.log
  * deleted 1 changesets from pushlog: 919c29ac42c0b25851d19be2d9d3883c45ba2ce4 (glob)
  * reordered 2 changesets in pushlog (glob)
  * --config 'extensions.mq=' strip -r 2 --no-backup exited 0 after * (glob)
#else
  $ cat .hg/blackbox.log
  * deleted 1 changesets from pushlog: 919c29ac42c0b25851d19be2d9d3883c45ba2ce4 (glob)
  * reordered 2 changesets in pushlog (glob)
  * --config extensions.mq= strip -r 2 --no-backup exited 0 after * (glob)
#endif
