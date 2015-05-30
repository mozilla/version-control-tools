  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > mq =
  > testrewrite = $TESTDIR/pylib/mozhg/mozhg/tests/testrewrite.py
  > EOF

  $ cat > obs.py << EOF
  > import mercurial.obsolete
  > mercurial.obsolete._enabled = True
  > EOF

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg commit -A -m initial
  adding foo
  $ hg phase --public -r 0

Attempting to rewrite in the middle of another operation results in error

  $ touch .hg/graftstate
  $ hg rewritemessage 0
  abort: graft in progress
  (use 'hg graft --continue' or 'hg update' to abort)
  [255]

  $ rm .hg/graftstate

Attempting to change a file during rewrite aborts (for now)

  $ hg rewritechangefile 0
  transaction abort!
  rollback completed
  abort: we do not allow replacements to modify files
  [255]

Attempting to rewrite a dirty working copy base results in error

  $ echo dirty > foo
  $ hg rewritemessage 0
  abort: uncommitted changes
  [255]

Smoke test rewrite a single changeset

  $ echo smoke > foo
  $ hg commit -m 'single changeset'

  $ hg log --debug -r 1
  changeset:   1:51de7a989d7652509e4d1e71f6a7b1a8ff37851f
  tag:         tip
  phase:       draft
  parent:      0:96ee1d7354c4ad7372047672c36a1f561e3a6a4c
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    1:658ef23369e7bc36bfa24eb985cf598676dca2fc
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  single changeset
  
  

  $ hg rewritemessage 1
  saved backup bundle to $TESTTMP/repo/.hg/strip-backup/51de7a989d76*-replacing.hg (glob)

  $ hg log -r .
  changeset:   1:4f5daa677d00
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     single changeset
  

  $ hg log -G
  @  changeset:   1:4f5daa677d00
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     single changeset
  |
  o  changeset:   0:96ee1d7354c4
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

  $ hg log --debug -r 1
  changeset:   1:4f5daa677d005fba9033f64f5e48e6b4ddd7704b
  tag:         tip
  phase:       draft
  parent:      0:96ee1d7354c4ad7372047672c36a1f561e3a6a4c
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    1:658ef23369e7bc36bfa24eb985cf598676dca2fc
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  single changeset
  0
  
  

Rewrite multiple changesets with no children

  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ echo 1 > foo
  $ hg commit -m 'multiple 1'
  created new head
  $ echo 2 > foo
  $ hg commit -m 'multiple 2'
  $ echo 3 > foo
  $ hg commit -m 'multiple 3'

  $ hg log --debug -r 2::
  changeset:   2:4d1ad76481c5796483bdc6a8ffe21d8fe106e5c7
  phase:       draft
  parent:      0:96ee1d7354c4ad7372047672c36a1f561e3a6a4c
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    2:93c70231c88572966b1059f6d4b93c9fe6703310
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  multiple 1
  
  
  changeset:   3:efda185d6a39ee01cb73a274ee7ee42cd53bc4b3
  phase:       draft
  parent:      2:4d1ad76481c5796483bdc6a8ffe21d8fe106e5c7
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    3:2b85f28d5b2028ea1eb72fd1912b8a1d0bc34da2
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  multiple 2
  
  
  changeset:   4:1daa37121b143876cea7f27f6ba9cee90b716644
  tag:         tip
  phase:       draft
  parent:      3:efda185d6a39ee01cb73a274ee7ee42cd53bc4b3
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    4:64c117e71e3638d9dc15beab13a7d4e61ba70764
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  multiple 3
  
  

  $ hg rewritemessage 2::
  saved backup bundle to $TESTTMP/repo/.hg/strip-backup/1daa37121b14*-replacing.hg (glob)

  $ hg log -G
  @  changeset:   4:100678c1b37f
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     multiple 3
  |
  o  changeset:   3:ac69ca483019
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     multiple 2
  |
  o  changeset:   2:6b0078365c16
  |  parent:      0:96ee1d7354c4
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     multiple 1
  |
  | o  changeset:   1:4f5daa677d00
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     single changeset
  |
  o  changeset:   0:96ee1d7354c4
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial
  

  $ hg log --debug -r 2::
  changeset:   2:6b0078365c16ff6d90a2124b3b96c49b95304f20
  phase:       draft
  parent:      0:96ee1d7354c4ad7372047672c36a1f561e3a6a4c
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    2:93c70231c88572966b1059f6d4b93c9fe6703310
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  multiple 1
  0
  
  
  changeset:   3:ac69ca4830192b10fb86594d0f3034795b794c52
  phase:       draft
  parent:      2:6b0078365c16ff6d90a2124b3b96c49b95304f20
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    3:2b85f28d5b2028ea1eb72fd1912b8a1d0bc34da2
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  multiple 2
  1
  
  
  changeset:   4:100678c1b37f51ab0cb7a7ad27aed6977bd74acc
  tag:         tip
  phase:       draft
  parent:      3:ac69ca4830192b10fb86594d0f3034795b794c52
  parent:      -1:0000000000000000000000000000000000000000
  manifest:    4:64c117e71e3638d9dc15beab13a7d4e61ba70764
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  files:       foo
  extra:       branch=default
  description:
  multiple 3
  2
  
  

Children are rebased automatically

  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ echo 1 > foo
  $ hg commit -m base
  created new head
  $ echo b1_1 > foo
  $ hg commit -m 'branch 1 commit 1'
  $ echo b1_2 > foo
  $ hg commit -m 'branch 1 commit 2'
  $ hg up -r 9834cc961a26
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo b2_1 > foo
  $ hg commit -m 'branch 2 commit 1'
  created new head
  $ echo b2_2 > foo
  $ hg commit -m 'branch 2 commit 2'

  $ hg log -G -r 5:
  @  changeset:   9:5658df40aea0
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     branch 2 commit 2
  |
  o  changeset:   8:10d2e0f9df33
  |  parent:      5:9834cc961a26
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     branch 2 commit 1
  |
  | o  changeset:   7:f2cc91c7c107
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     branch 1 commit 2
  | |
  | o  changeset:   6:67fabc181c37
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     branch 1 commit 1
  |
  o  changeset:   5:9834cc961a26
  |  parent:      0:96ee1d7354c4
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     base
  |

  $ hg rewritemessage 9834cc961a26::67fabc181c37
  saved backup bundle to $TESTTMP/repo/.hg/strip-backup/5658df40aea0*-replacing.hg (glob)

  $ hg log -G -r 5: --debug
  @  changeset:   9:69aa52704031593eb89782d661312e37ec7db452
  |  tag:         tip
  |  phase:       draft
  |  parent:      8:dcae339901b4908e3bc11170a832e1cb01e10196
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    8:4317639984d05c5b2b5744800237be45b528060b
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  extra:       branch=default
  |  description:
  |  branch 2 commit 2
  |
  |
  o  changeset:   8:dcae339901b4908e3bc11170a832e1cb01e10196
  |  phase:       draft
  |  parent:      5:f9d897b602f9832703568507b9c240f1cec64688
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    7:d9b1ab986657895e23c65da93b665d8cf87d983c
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  extra:       branch=default
  |  description:
  |  branch 2 commit 1
  |
  |
  | o  changeset:   7:7aa335078f5bcabed61562d1901a0c181b836566
  | |  phase:       draft
  | |  parent:      6:fafcf26cf5afa24d69276cd3f5e12a89cd4153d8
  | |  parent:      -1:0000000000000000000000000000000000000000
  | |  manifest:    6:99223e52834b792f7e7bad815e22ff18b5df7355
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  extra:       branch=default
  | |  description:
  | |  branch 1 commit 2
  | |
  | |
  | o  changeset:   6:fafcf26cf5afa24d69276cd3f5e12a89cd4153d8
  |/   phase:       draft
  |    parent:      5:f9d897b602f9832703568507b9c240f1cec64688
  |    parent:      -1:0000000000000000000000000000000000000000
  |    manifest:    5:c162654d82a03e0ea5e390d6091b7fa46f7ac901
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    files:       foo
  |    extra:       branch=default
  |    description:
  |    branch 1 commit 1
  |    1
  |
  |
  o  changeset:   5:f9d897b602f9832703568507b9c240f1cec64688
  |  phase:       draft
  |  parent:      0:96ee1d7354c4ad7372047672c36a1f561e3a6a4c
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    2:93c70231c88572966b1059f6d4b93c9fe6703310
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  files:       foo
  |  extra:       branch=default
  |  description:
  |  base
  |  0
  |
  |

Working copy changes to rebased children cause abort

  $ echo modify > foo
  $ hg rewritemessage f9d897b602f9::fafcf26cf5af
  abort: uncommitted changes
  [255]

  $ hg revert -C foo

Phase of commits is preserved

  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ echo secret1 > foo
  $ hg commit -m 'secret 1'
  created new head
  $ hg phase --force --secret -r 10
  $ echo secret2 > foo
  $ hg commit -m 'secret 2'
  $ hg log -T '{rev}:{phase}\n' -r 10::
  10:secret
  11:secret

  $ hg rewritemessage 10
  saved backup bundle to $TESTTMP/repo/.hg/strip-backup/1bed226c2afc*-replacing.hg (glob)

  $ hg log -T '{rev}:{phase}\n' -r 10::
  10:secret
  11:secret

Obsolescence, not stripping, should occur when enabled

  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo obs1 > foo
  $ hg commit -m 'obsolete 1'
  created new head
  $ echo obs2 > foo
  $ hg commit -m 'obsolete 2'

  $ hg --config extensions.obs=$TESTTMP/obs.py rewritemessage 12

  $ hg --config extensions.obs=$TESTTMP/obs.py log -G -r 11:
  @  changeset:   15:bbfe981e7c92
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     obsolete 2
  |
  o  changeset:   14:bc9e3a9b7283
  |  parent:      0:96ee1d7354c4
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     obsolete 1
  |
  | o  changeset:   11:94879ae69a6f
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     secret 2
  | |

  $ hg --config extensions.obs=$TESTTMP/obs.py --hidden log -G -r 11:
  @  changeset:   15:bbfe981e7c92
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     obsolete 2
  |
  o  changeset:   14:bc9e3a9b7283
  |  parent:      0:96ee1d7354c4
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     obsolete 1
  |
  | x  changeset:   13:7ceaf29d1ae9
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     obsolete 2
  | |
  | x  changeset:   12:da0a718bed60
  |/   parent:      0:96ee1d7354c4
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     obsolete 1
  |
  | o  changeset:   11:94879ae69a6f
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     secret 2
  | |

  $ rm .hg/store/obsstore

Bookmarks on rewritten changesets should be moved

  $ hg up -r 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg bookmark initial
  $ hg bookmark @
  $ echo bm_base > foo
  $ hg commit -m 'bookmark base'
  created new head
  $ hg bookmark bm1
  $ echo bm1_1 > foo
  $ hg commit -m 'bm1 commit 1'
  $ echo bm1_2 > foo
  $ hg commit -m 'bm1 commit 2'
  $ hg up 8e65b6d54ce1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bm1)
  $ hg bookmark bm2
  $ echo bm2_1 > foo
  $ hg commit -m 'bm2 commit 1'
  created new head
  $ echo bm2_2 > foo
  $ hg commit -m 'bm2 commit 2'

  $ hg bookmarks
     @                         16:8e65b6d54ce1
     bm1                       18:090fd562f21c
   * bm2                       20:94502083ee7f
     initial                   0:96ee1d7354c4

  $ hg rewritemessage @
  saved backup bundle to $TESTTMP/repo/.hg/strip-backup/94502083ee7f*-replacing.hg (glob)

  $ hg bookmarks
     @                         16:1eccffc1b352
     bm1                       18:c558d9c0729a
   * bm2                       20:09adebe5d91f
     initial                   0:96ee1d7354c4

  $ hg up 09adebe5d91f
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark bm2)

Rewritten MQ patches should retain metadata

  $ echo mq1 > foo
  $ hg qnew -d '0 0' -m 'patch 1' patch-1
  $ echo mq2 > foo
  $ hg qnew -d '0 0' -m 'patch 2' patch-2

  $ cat .hg/patches/status
  a5e67d6e497c00fb8adeeb7323a296c5213f2f1e:patch-1
  3a73c2aaa65fd57219d9aab020f2ae39e074bc9f:patch-2

  $ hg log -G -r 09adebe5d91f::
  @  changeset:   22:3a73c2aaa65f
  |  tag:         patch-2
  |  tag:         qtip
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     patch 2
  |
  o  changeset:   21:a5e67d6e497c
  |  tag:         patch-1
  |  tag:         qbase
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     patch 1
  |
  o  changeset:   20:09adebe5d91f
  |  bookmark:    bm2
  |  tag:         qparent
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     bm2 commit 2
  |

  $ hg rewritemessage a5e67d6e497c
  saved backup bundle to $TESTTMP/repo/.hg/strip-backup/3a73c2aaa65f*-replacing.hg (glob)

  $ hg log -G -r 09adebe5d91f::
  @  changeset:   22:abed09a143d6
  |  tag:         patch-2
  |  tag:         qtip
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     patch 2
  |
  o  changeset:   21:288e8c606a3f
  |  tag:         patch-1
  |  tag:         qbase
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     patch 1
  |
  o  changeset:   20:09adebe5d91f
  |  bookmark:    bm2
  |  tag:         qparent
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     bm2 commit 2
  |

  $ cat .hg/patches/status
  288e8c606a3f24683f43178379cdd554cd38c058:patch-1
  abed09a143d6ec1a5a225abfea720ba41eff3b7c:patch-2
