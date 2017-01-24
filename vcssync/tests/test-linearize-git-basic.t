  $ . $TESTDIR/vcssync/tests/helpers.sh

Create a Git repo with a simple merge

  $ git init grepo0
  Initialized empty Git repository in $TESTTMP/grepo0/.git/
  $ cd grepo0
  $ touch foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) a547cc0] initial
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 foo
  $ git checkout -b head1
  Switched to a new branch 'head1'
  $ touch file0
  $ git add file0
  $ git commit -m 'add file0'
  [head1 48fba69] add file0
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 file0
  $ git checkout master
  Switched to branch 'master'
  $ touch file1
  $ git add file1
  $ git commit -m 'add file1'
  [master c37ea67] add file1
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 file1
  $ git merge head1
  Merge made by the 'recursive' strategy.
   file0 | 0
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 file0

  $ git log --graph --format=oneline
  *   9127cbf8ed74dd362cf28e37e8df7864df3057e3 Merge branch 'head1'
  |\  
  | * 48fba69d25d8ec2d06c8d0a00851d109acd7d986 add file0
  * | c37ea67cfc02a686d402594235bcba334fb727af add file1
  |/  
  * a547cc07d30f025e022b27310c713705158c21b4 initial

  $ git for-each-ref
  48fba69d25d8ec2d06c8d0a00851d109acd7d986 commit	refs/heads/head1
  9127cbf8ed74dd362cf28e37e8df7864df3057e3 commit	refs/heads/master

Linearized repo should have no merges

  $ linearize-git . heads/master
  linearizing 3 commits from heads/master (a547cc07d30f025e022b27310c713705158c21b4 to 9127cbf8ed74dd362cf28e37e8df7864df3057e3)
  1/3 a547cc07d30f025e022b27310c713705158c21b4 initial
  2/3 c37ea67cfc02a686d402594235bcba334fb727af add file1
  3/3 9127cbf8ed74dd362cf28e37e8df7864df3057e3 Merge branch 'head1'
  heads/master converted; original: 9127cbf8ed74dd362cf28e37e8df7864df3057e3; rewritten: 4a8e25bc50dc5e927f209e1cbac8a7c0346b72b7

  $ git log --graph --format=oneline convert/dest/heads/master
  * 4a8e25bc50dc5e927f209e1cbac8a7c0346b72b7 Merge branch 'head1'
  * c37ea67cfc02a686d402594235bcba334fb727af add file1
  * a547cc07d30f025e022b27310c713705158c21b4 initial

Original refs should be untouched, new tracking refs should be added

  $ git for-each-ref
  4a8e25bc50dc5e927f209e1cbac8a7c0346b72b7 commit	refs/convert/dest/heads/master
  9127cbf8ed74dd362cf28e37e8df7864df3057e3 commit	refs/convert/source/heads/master
  48fba69d25d8ec2d06c8d0a00851d109acd7d986 commit	refs/heads/head1
  9127cbf8ed74dd362cf28e37e8df7864df3057e3 commit	refs/heads/master

Linearize with no changes should no-op

  $ linearize-git . heads/master
  no new commits to linearize; not doing anything

Add more commits to the source repository

  $ touch file2
  $ git add file2
  $ git commit -m 'add file2'
  [master 622273f] add file2
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 file2
  $ touch file3
  $ git add file3
  $ git commit -m 'add file3'
  [master e6c4fa0] add file3
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 file3

Incremental linearize should only convert new commits, graft on top of existing conversion

  $ git for-each-ref
  4a8e25bc50dc5e927f209e1cbac8a7c0346b72b7 commit	refs/convert/dest/heads/master
  9127cbf8ed74dd362cf28e37e8df7864df3057e3 commit	refs/convert/source/heads/master
  48fba69d25d8ec2d06c8d0a00851d109acd7d986 commit	refs/heads/head1
  e6c4fa028c4bbb545d8b72667cf224e2141d88e7 commit	refs/heads/master

  $ linearize-git . heads/master
  linearizing 2 commits from heads/master (622273f903fba1c0fabe939ec34a61e804fa66cf to e6c4fa028c4bbb545d8b72667cf224e2141d88e7)
  1/2 622273f903fba1c0fabe939ec34a61e804fa66cf add file2
  2/2 e6c4fa028c4bbb545d8b72667cf224e2141d88e7 add file3
  heads/master converted; original: e6c4fa028c4bbb545d8b72667cf224e2141d88e7; rewritten: dd15e055c3525362c7d61d09f0e71be97d730415

  $ git for-each-ref
  dd15e055c3525362c7d61d09f0e71be97d730415 commit	refs/convert/dest/heads/master
  e6c4fa028c4bbb545d8b72667cf224e2141d88e7 commit	refs/convert/source/heads/master
  48fba69d25d8ec2d06c8d0a00851d109acd7d986 commit	refs/heads/head1
  e6c4fa028c4bbb545d8b72667cf224e2141d88e7 commit	refs/heads/master

  $ git log --graph --format=oneline refs/heads/master
  * e6c4fa028c4bbb545d8b72667cf224e2141d88e7 add file3
  * 622273f903fba1c0fabe939ec34a61e804fa66cf add file2
  *   9127cbf8ed74dd362cf28e37e8df7864df3057e3 Merge branch 'head1'
  |\  
  | * 48fba69d25d8ec2d06c8d0a00851d109acd7d986 add file0
  * | c37ea67cfc02a686d402594235bcba334fb727af add file1
  |/  
  * a547cc07d30f025e022b27310c713705158c21b4 initial

  $ git log --graph --format=oneline refs/convert/dest/heads/master
  * dd15e055c3525362c7d61d09f0e71be97d730415 add file3
  * 70d34f749be26b16519ea65aac6d9851040d1bd8 add file2
  * 4a8e25bc50dc5e927f209e1cbac8a7c0346b72b7 Merge branch 'head1'
  * c37ea67cfc02a686d402594235bcba334fb727af add file1
  * a547cc07d30f025e022b27310c713705158c21b4 initial

  $ git cat-file -p refs/convert/dest/heads/master^
  tree ba95d78c0a2301f6c6d095af7cbb5e0ee2254de3
  parent 4a8e25bc50dc5e927f209e1cbac8a7c0346b72b7
  author test <test@example.com> 0 +0000
  committer test <test@example.com> 0 +0000
  
  add file2

  $ git log --graph --format=oneline convert/dest/heads/master
  * dd15e055c3525362c7d61d09f0e71be97d730415 add file3
  * 70d34f749be26b16519ea65aac6d9851040d1bd8 add file2
  * 4a8e25bc50dc5e927f209e1cbac8a7c0346b72b7 Merge branch 'head1'
  * c37ea67cfc02a686d402594235bcba334fb727af add file1
  * a547cc07d30f025e022b27310c713705158c21b4 initial

Should no-op again

  $ linearize-git . heads/master
  no new commits to linearize; not doing anything
