#require hg41+

  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ standardgitrepo grepo > /dev/null 2>&1

  $ git --git-dir grepo/.git log --graph --format=oneline
  * a447b9b0ff25bf17daab1c7edae4a998eca0adac dummy commit 1 after merge
  *   fc30a4fbd1fe16d4c84ca50119e0c404c13967a3 Merge branch 'head2'
  |\  
  | * 7b4eab003357aaa2873a1976cb86f5c4a70f5f22 dummy commit 2 on head2
  | * 8b358b77dede1a070e1047874be3679a31a210c9 dummy commit 1 on head2
  * | 7a13658c4512ce4c99800417db933f4a1d3fdcb3 dummy commit 2 on master
  * | 85fd94699e69ce4d2d55171078541c1019f111e4 dummy commit 1 on master
  |/  
  * ecba8e9490aa2f14345a2da0da62631928ff2968 create file1-20, file1-50 and file1-80 as copies with mods
  * 2b77427ac0fe55e172d4174530c9bcc4b2544ff6 copy file0-moved and rename source
  * 9fea386651d90b505d5d1fa2e70c465562b04c7d move file0 to file0-moved
  * 4d2fb4a1b4defb3cdf7abb52d9d3c91245d26194 copy file0 to file0-copy1 and file0-copy2
  * 73617395f86af21dde35a52e6149c8e1aac4e68f copy file0 to file0-copy0
  * 6044be85e82c72f9115362f88c42ce94016e8718 add file0 and file1
  * dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial

Basic git to hg linearize works

  $ linearize-git-to-hg file://$TESTTMP/grepo master grepo-source grepo-dest
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

Subsequent invocation no-ops

  $ linearize-git-to-hg file://$TESTTMP/grepo master grepo-source grepo-dest
  no new commits to linearize; not doing anything
  all Git commits have already been converted; not doing anything
