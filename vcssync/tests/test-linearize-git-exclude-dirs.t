  $ . $TESTDIR/vcssync/tests/helpers.sh

Create a Git repo with files we wish to prune

  $ git init repo0
  Initialized empty Git repository in $TESTTMP/repo0/.git/
  $ cd repo0
  $ touch foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) a547cc0] initial
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 foo
  $ git checkout -b head1
  Switched to a new branch 'head1'
  $ mkdir dir0 dir1 dir2
  $ touch dir0/file0 dir1/file0 dir2/file0
  $ git add -A
  $ git commit -m 'add file0s'
  [head1 db8c4de] add file0s
   3 files changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir0/file0
   create mode 100644 dir1/file0
   create mode 100644 dir2/file0
  $ git checkout master
  Switched to branch 'master'
  $ mkdir dir0 dir1 dir2
  $ touch dir0/file1 dir1/file1 dir2/file1
  $ git add -A
  $ git commit -m 'add file1s'
  [master 0ac77c9] add file1s
   3 files changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir0/file1
   create mode 100644 dir1/file1
   create mode 100644 dir2/file1
  $ touch dir0/file2
  $ git add -A
  $ git commit -m 'add dir0/file2'
  [master b7b3abc] add dir0/file2
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir0/file2
  $ git checkout master
  Already on 'master'
  $ git merge head1
  Merge made by the 'recursive' strategy.
   dir0/file0 | 0
   dir1/file0 | 0
   dir2/file0 | 0
   3 files changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir0/file0
   create mode 100644 dir1/file0
   create mode 100644 dir2/file0

  $ git log --graph --format=oneline
  *   e9fb4537517445c07d491482211919591e4dae45 Merge branch 'head1'
  |\  
  | * db8c4dec7798ea623eeb989c3112e9e96767a722 add file0s
  * | b7b3abcd50597761f65c0a11846de6ebc98cc5b7 add dir0/file2
  * | 0ac77c9293242a70f71defcee37a74659207b19e add file1s
  |/  
  * a547cc07d30f025e022b27310c713705158c21b4 initial

  $ git for-each-ref
  db8c4dec7798ea623eeb989c3112e9e96767a722 commit	refs/heads/head1
  e9fb4537517445c07d491482211919591e4dae45 commit	refs/heads/master

Directories can be excluded when linearizing

  $ linearize-git --exclude-dir dir2 . heads/master
  linearizing 4 commits from heads/master (a547cc07d30f025e022b27310c713705158c21b4 to e9fb4537517445c07d491482211919591e4dae45)
  1/4 a547cc07d30f025e022b27310c713705158c21b4 initial
  2/4 0ac77c9293242a70f71defcee37a74659207b19e add file1s
  3/4 b7b3abcd50597761f65c0a11846de6ebc98cc5b7 add dir0/file2
  4/4 e9fb4537517445c07d491482211919591e4dae45 Merge branch 'head1'
  4 commits from heads/master converted; original: e9fb4537517445c07d491482211919591e4dae45; rewritten: d017a118a5429ca800345e6f14e1a61f6f613b57

  $ git show -m refs/convert/dest/heads/master
  commit d017a118a5429ca800345e6f14e1a61f6f613b57
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge branch 'head1'
  
  diff --git a/dir0/file0 b/dir0/file0
  new file mode 100644
  index 0000000..e69de29
  diff --git a/dir1/file0 b/dir1/file0
  new file mode 100644
  index 0000000..e69de29

--exclude-dir works multiple times

  $ git update-ref -d refs/convert/source/heads/master
  $ git update-ref -d refs/convert/dest/heads/master
  $ linearize-git --exclude-dir dir0 --exclude-dir dir1 . heads/master
  linearizing 4 commits from heads/master (a547cc07d30f025e022b27310c713705158c21b4 to e9fb4537517445c07d491482211919591e4dae45)
  1/4 a547cc07d30f025e022b27310c713705158c21b4 initial
  2/4 0ac77c9293242a70f71defcee37a74659207b19e add file1s
  3/4 b7b3abcd50597761f65c0a11846de6ebc98cc5b7 add dir0/file2
  dropping b7b3abcd50597761f65c0a11846de6ebc98cc5b7 because no tree changes
  4/4 e9fb4537517445c07d491482211919591e4dae45 Merge branch 'head1'
  3 commits from heads/master converted; original: e9fb4537517445c07d491482211919591e4dae45; rewritten: adc3f0cd6e97a4aaded01d4c68119b7566807b07
  $ git log --graph --format=oneline refs/convert/dest/heads/master
  * adc3f0cd6e97a4aaded01d4c68119b7566807b07 Merge branch 'head1'
  * 925f1eab825ed50a1f80058c6a1f220c009a8bfd add file1s
  * a547cc07d30f025e022b27310c713705158c21b4 initial
  $ git show -m refs/convert/dest/heads/master
  commit adc3f0cd6e97a4aaded01d4c68119b7566807b07
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge branch 'head1'
  
  diff --git a/dir2/file0 b/dir2/file0
  new file mode 100644
  index 0000000..e69de29

  $ cd ..

Excluding an intermediate directory works

  $ git init repo1
  Initialized empty Git repository in $TESTTMP/repo1/.git/
  $ cd repo1
  $ mkdir -p dir0/subdir0 dir0/subdir1 dir1 dir2/subdir0 dir2/subdir1
  $ touch dir0/subdir0/file0
  $ touch dir0/file0
  $ touch dir0/subdir1/file0
  $ touch dir1/file0
  $ touch dir2/file0
  $ touch dir2/subdir0/file0
  $ touch dir2/subdir1/file0

  $ git add --all
  $ git commit -m initial
  [master (root-commit) 1190a97] initial
   7 files changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir0/file0
   create mode 100644 dir0/subdir0/file0
   create mode 100644 dir0/subdir1/file0
   create mode 100644 dir1/file0
   create mode 100644 dir2/file0
   create mode 100644 dir2/subdir0/file0
   create mode 100644 dir2/subdir1/file0
  $ git branch master2 HEAD

  $ linearize-git --exclude-dir dir0/subdir0 . heads/master
  linearizing 1 commits from heads/master (1190a970be8401aac3e4773332dd10f78e4141f2 to 1190a970be8401aac3e4773332dd10f78e4141f2)
  1/1 1190a970be8401aac3e4773332dd10f78e4141f2 initial
  1 commits from heads/master converted; original: 1190a970be8401aac3e4773332dd10f78e4141f2; rewritten: 2c092d0f01a4a443e2120c897bc7f1fa3b94c3c5

  $ git ls-tree -r -t refs/convert/dest/heads/master
  040000 tree a5a64b4a01d3e32ff0050e6323ff8abcbce0ded7	dir0
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir0/file0
  040000 tree 09767bd3484e22b41138116992cc1cb5bc45fb7f	dir0/subdir1
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir0/subdir1/file0
  040000 tree 09767bd3484e22b41138116992cc1cb5bc45fb7f	dir1
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir1/file0
  040000 tree 871a0c072ebc416415cc682bbda94e7948c8f568	dir2
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir2/file0
  040000 tree 09767bd3484e22b41138116992cc1cb5bc45fb7f	dir2/subdir0
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir2/subdir0/file0
  040000 tree 09767bd3484e22b41138116992cc1cb5bc45fb7f	dir2/subdir1
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir2/subdir1/file0

  $ linearize-git --exclude-dir dir1 --exclude-dir dir2/subdir0 . heads/master2
  linearizing 1 commits from heads/master2 (1190a970be8401aac3e4773332dd10f78e4141f2 to 1190a970be8401aac3e4773332dd10f78e4141f2)
  1/1 1190a970be8401aac3e4773332dd10f78e4141f2 initial
  1 commits from heads/master2 converted; original: 1190a970be8401aac3e4773332dd10f78e4141f2; rewritten: d46fb3759f69a9ed2c56395653cf3e61fad6f5e7

  $ git ls-tree -r -t refs/convert/dest/heads/master2
  040000 tree 871a0c072ebc416415cc682bbda94e7948c8f568	dir0
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir0/file0
  040000 tree 09767bd3484e22b41138116992cc1cb5bc45fb7f	dir0/subdir0
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir0/subdir0/file0
  040000 tree 09767bd3484e22b41138116992cc1cb5bc45fb7f	dir0/subdir1
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir0/subdir1/file0
  040000 tree a5a64b4a01d3e32ff0050e6323ff8abcbce0ded7	dir2
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir2/file0
  040000 tree 09767bd3484e22b41138116992cc1cb5bc45fb7f	dir2/subdir1
  100644 blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391	dir2/subdir1/file0
