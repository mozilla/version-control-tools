#require hg41+

  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ standardgitrepo grepo > /dev/null 2>&1

  $ git init --bare grepo-mirror
  Initialized empty Git repository in $TESTTMP/grepo-mirror/

--git-push-url will mirror the local Git repo to a remote after changes

  $ linearize-git-to-hg --git-push-url file://$TESTTMP/grepo-mirror file://$TESTTMP/grepo master grepo-source hgrepo-dest
  Initialized empty Git repository in $TESTTMP/grepo-source/
  From file://$TESTTMP/grepo
   * [new branch]      master     -> master
  To file://$TESTTMP/grepo-mirror
   * [new branch]      master -> master
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
  To file://$TESTTMP/grepo-mirror
   * [new branch]      refs/convert/dest/heads/master -> refs/convert/dest/heads/master
   * [new branch]      refs/convert/source/heads/master -> refs/convert/source/heads/master
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
  11 Git commits converted to Mercurial; previous tip: -1:0000000000000000000000000000000000000000; current tip: 10:74b93af557b18fa56b0e9fad513ef9da1a1d950f

All refs from local Git repo should be in mirror

  $ git -C grepo-source for-each-ref
  aea30981234cf6848489e0ccf541fbf902b27aca commit	refs/convert/dest/heads/master
  a447b9b0ff25bf17daab1c7edae4a998eca0adac commit	refs/convert/source/heads/master
  a447b9b0ff25bf17daab1c7edae4a998eca0adac commit	refs/heads/master

  $ git -C grepo-mirror for-each-ref
  aea30981234cf6848489e0ccf541fbf902b27aca commit	refs/convert/dest/heads/master
  a447b9b0ff25bf17daab1c7edae4a998eca0adac commit	refs/convert/source/heads/master
  a447b9b0ff25bf17daab1c7edae4a998eca0adac commit	refs/heads/master

Incremental conversion will keep Git repo in sync

  $ cd grepo
  $ touch incremental
  $ git add incremental
  $ git commit -m 'add incremental'
  [master 4040c16] add incremental
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 incremental
  $ cd ..

  $ linearize-git-to-hg --git-push-url file://$TESTTMP/grepo-mirror file://$TESTTMP/grepo master grepo-source hgrepo-dest
  From file://$TESTTMP/grepo
     a447b9b..4040c16  master     -> master
  To file://$TESTTMP/grepo-mirror
     a447b9b..4040c16  master -> master
  linearizing 1 commits from heads/master (4040c1631489c25dd4e0fd1606c4a065e1a24194 to 4040c1631489c25dd4e0fd1606c4a065e1a24194)
  1/1 4040c1631489c25dd4e0fd1606c4a065e1a24194 add incremental
  1 commits from heads/master converted; original: 4040c1631489c25dd4e0fd1606c4a065e1a24194; rewritten: d6ec61184bff36a58159341c2584f3cda9dd0b58
  To file://$TESTTMP/grepo-mirror
     aea3098..d6ec611  refs/convert/dest/heads/master -> refs/convert/dest/heads/master
     a447b9b..4040c16  refs/convert/source/heads/master -> refs/convert/source/heads/master
  converting 1 Git commits
  scanning source...
  sorting...
  converting...
  0 add incremental
  1 Git commits converted to Mercurial; previous tip: 10:74b93af557b18fa56b0e9fad513ef9da1a1d950f; current tip: 11:b53d6fba975e3face586964aace142716b2191a7

  $ git -C grepo-source for-each-ref
  d6ec61184bff36a58159341c2584f3cda9dd0b58 commit	refs/convert/dest/heads/master
  4040c1631489c25dd4e0fd1606c4a065e1a24194 commit	refs/convert/source/heads/master
  4040c1631489c25dd4e0fd1606c4a065e1a24194 commit	refs/heads/master

  $ git -C grepo-mirror for-each-ref
  d6ec61184bff36a58159341c2584f3cda9dd0b58 commit	refs/convert/dest/heads/master
  4040c1631489c25dd4e0fd1606c4a065e1a24194 commit	refs/convert/source/heads/master
  4040c1631489c25dd4e0fd1606c4a065e1a24194 commit	refs/heads/master
