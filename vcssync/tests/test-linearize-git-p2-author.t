  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ git init grepo0
  Initialized empty Git repository in $TESTTMP/grepo0/.git/

  $ cd grepo0
  $ echo 0 > foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) dbd62b8] initial
   1 file changed, 1 insertion(+)
   create mode 100644 foo
  $ git branch feature-branch

  $ echo 1 > foo
  $ git add foo
  $ git commit -m 1
  [master 3859ebb] 1
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git checkout feature-branch
  Switched to branch 'feature-branch'
  $ echo 2 > bar
  $ git add bar
  $ GIT_AUTHOR_NAME='Another Author' GIT_AUTHOR_EMAIL='another@example.com' git commit -m 2
  [feature-branch d2b9537] 2
   Author: Another Author <another@example.com>
   1 file changed, 1 insertion(+)
   create mode 100644 bar

  $ git checkout master
  Switched to branch 'master'
  $ git merge feature-branch
  Merge made by the 'recursive' strategy.
   bar | 1 +
   1 file changed, 1 insertion(+)
   create mode 100644 bar

Using p2 parent for rewritten merge commit works

  $ linearize-git --use-p2-author . heads/master
  linearizing 3 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to 1d7609530bb5efe1b11c2be19368669f9892e055)
  1/3 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/3 3859ebb89b4a8ef66d455f7f0d550a8a609154da 1
  3/3 1d7609530bb5efe1b11c2be19368669f9892e055 Merge branch 'feature-branch'
  3 commits from heads/master converted; original: 1d7609530bb5efe1b11c2be19368669f9892e055; rewritten: 534e8c7588c35783ba75712dc4549852a65ed720

  $ git log convert/dest/heads/master
  commit 534e8c7588c35783ba75712dc4549852a65ed720
  Author: Another Author <another@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge branch 'feature-branch'
  
  commit 3859ebb89b4a8ef66d455f7f0d550a8a609154da
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      1
  
  commit dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial
