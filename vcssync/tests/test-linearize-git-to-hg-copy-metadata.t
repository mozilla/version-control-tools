#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ cat >> $HGRCPATH << EOF
  > [diff]
  > git = true
  > EOF

  $ standardgitrepo grepo > /dev/null 2>&1

  $ linearize-git-to-hg file://$TESTTMP/grepo master grepo-source grepo-dest-default
  Initialized empty Git repository in $TESTTMP/grepo-source/
  From file://$TESTTMP/grepo
   * [new branch]      master     -> master
  linearizing 11 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to a447b9b0ff25bf17daab1c7edae4a998eca0adac)
  1/11 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/11 6044be85e82c72f9115362f88c42ce94016e8718 add file0 and file1
  3/11 73617395f86af21dde35a52e6149c8e1aac4e68f copy file0 to file0-copy0
  4/11 4d2fb4a1b4defb3cdf7abb52d9d3c91245d26194 copy file0 to file0-copy1 and file0-copy2
  5/11 9fea386651d90b505d5d1fa2e70c465562b04c7d move file0 to file0-moved
  6/11 2b77427ac0fe55e172d4174530c9bcc4b2544ff6 copy file0-moved and rename source
  7/11 ecba8e9490aa2f14345a2da0da62631928ff2968 create file1-20, file1-50 and file1-80 as copies with mods
  8/11 85fd94699e69ce4d2d55171078541c1019f111e4 dummy commit 1 on master
  9/11 7a13658c4512ce4c99800417db933f4a1d3fdcb3 dummy commit 2 on master
  10/11 fc30a4fbd1fe16d4c84ca50119e0c404c13967a3 Merge branch 'head2'
  11/11 a447b9b0ff25bf17daab1c7edae4a998eca0adac dummy commit 1 after merge
  11 commits from heads/master converted; original: a447b9b0ff25bf17daab1c7edae4a998eca0adac; rewritten: aea30981234cf6848489e0ccf541fbf902b27aca
  converting 11 Git commits
  scanning source...
  sorting...
  converting...
  10 initial
  9 add file0 and file1
  8 copy file0 to file0-copy0
  7 copy file0 to file0-copy1 and file0-copy2
  6 move file0 to file0-moved
  5 copy file0-moved and rename source
  4 create file1-20, file1-50 and file1-80 as copies with mods
  3 dummy commit 1 on master
  2 dummy commit 2 on master
  1 Merge branch 'head2'
  0 dummy commit 1 after merge
  11 Git commits converted to Mercurial; previous tip: -1:0000000000000000000000000000000000000000; current tip: 10:7d80acaa161029d9e746e3125e7cc0916406403f

Move annotation should be preserved automatically

  $ hg -R grepo-dest-default export 4
  # HG changeset patch
  # User test <test@example.com>
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 87dc2703fa8274f2cbb4368fc5cd21dd6b891283
  # Parent  cf8b7b151d770811c9bdd22ecf9252ce497ac902
  move file0 to file0-moved
  
  diff --git a/file0 b/file0-moved
  rename from file0
  rename to file0-moved

Copy annotation should be preserved automatically

  $ hg -R grepo-dest-default export 5
  # HG changeset patch
  # User test <test@example.com>
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 9448d0d725df65d963f7c9772f656c1777eff035
  # Parent  87dc2703fa8274f2cbb4368fc5cd21dd6b891283
  copy file0-moved and rename source
  
  diff --git a/file0-moved b/file0-copied-with-move
  rename from file0-moved
  rename to file0-copied-with-move
  diff --git a/file0-moved b/file0-moved-with-copy
  copy from file0-moved
  copy to file0-moved-with-copy

Normal copy won't be detected if source not modified

  $ hg -R grepo-dest-default export 2
  # HG changeset patch
  # User test <test@example.com>
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 0645166c54cc387ec7b451618db945e6921a2f05
  # Parent  39f28bdb42e2c48e9dff20d047ccba4d69bbf319
  copy file0 to file0-copy0
  
  diff --git a/file0-copy0 b/file0-copy0
  new file mode 100644
  --- /dev/null
  +++ b/file0-copy0
  @@ -0,0 +1,11 @@
  +file0 0
  +file0 1
  +file0 2
  +file0 3
  +file0 4
  +file0 5
  +file0 6
  +file0 7
  +file0 8
  +file0 9
  +file0 10

--find-copies-harder will find copies

  $ linearize-git-to-hg --find-copies-harder file://$TESTTMP/grepo master grepo-source grepo-dest-find-copy-harder > /dev/null 2>&1

  $ hg -R grepo-dest-find-copy-harder export 2
  # HG changeset patch
  # User test <test@example.com>
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID f793a24cb294215e734ba63f1741635927792532
  # Parent  39f28bdb42e2c48e9dff20d047ccba4d69bbf319
  copy file0 to file0-copy0
  
  diff --git a/file0 b/file0-copy0
  copy from file0
  copy to file0-copy0

Copy detection similarity is sane

  $ hg -R grepo-dest-find-copy-harder export 6
  # HG changeset patch
  # User test <test@example.com>
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 5c6526a3256267aa3530fef4d51387ec90b61b20
  # Parent  f16834370a2a91f32d16d537de3590fd2f86c3fb
  create file1-20, file1-50 and file1-80 as copies with mods
  
  diff --git a/file1-20 b/file1-20
  new file mode 100644
  --- /dev/null
  +++ b/file1-20
  @@ -0,0 +1,2 @@
  +file1 2
  +file1 7
  diff --git a/file1 b/file1-50
  copy from file1
  copy to file1-50
  --- a/file1
  +++ b/file1-50
  @@ -3,8 +3,3 @@
   file1 2
   file1 3
   file1 4
  -file1 5
  -file1 6
  -file1 7
  -file1 8
  -file1 9
  diff --git a/file1 b/file1-80
  copy from file1
  copy to file1-80
  --- a/file1
  +++ b/file1-80
  @@ -2,9 +2,7 @@
   file1 1
   file1 2
   file1 3
  -file1 4
   file1 5
   file1 6
   file1 7
  -file1 8
   file1 9

Increase similarity threshold removes copy annotation from file1-50

  $ linearize-git-to-hg --copy-similarity 70 --find-copies-harder file://$TESTTMP/grepo master grepo-source grepo-dest-similarity-70 > /dev/null 2>&1

  $ hg -R grepo-dest-similarity-70 export 6
  # HG changeset patch
  # User test <test@example.com>
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 65ca132d671b09006951d7b6f611cc6a7cc327c0
  # Parent  f16834370a2a91f32d16d537de3590fd2f86c3fb
  create file1-20, file1-50 and file1-80 as copies with mods
  
  diff --git a/file1-20 b/file1-20
  new file mode 100644
  --- /dev/null
  +++ b/file1-20
  @@ -0,0 +1,2 @@
  +file1 2
  +file1 7
  diff --git a/file1-50 b/file1-50
  new file mode 100644
  --- /dev/null
  +++ b/file1-50
  @@ -0,0 +1,5 @@
  +file1 0
  +file1 1
  +file1 2
  +file1 3
  +file1 4
  diff --git a/file1 b/file1-80
  copy from file1
  copy to file1-80
  --- a/file1
  +++ b/file1-80
  @@ -2,9 +2,7 @@
   file1 1
   file1 2
   file1 3
  -file1 4
   file1 5
   file1 6
   file1 7
  -file1 8
   file1 9
