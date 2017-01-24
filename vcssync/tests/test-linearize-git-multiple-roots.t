  $ . $TESTDIR/vcssync/tests/helpers.sh

Create a Git repo with multiple heads

  $ git init grepo
  Initialized empty Git repository in $TESTTMP/grepo/.git/
  $ cd grepo

  $ touch foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) a547cc0] initial
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 foo

  $ echo 0 > file0
  $ echo 0 > file1
  $ echo 0 > file2
  $ git add file0 file1 file2
  $ git commit -m 'add file0 file1 file2'
  [master 14ed61b] add file0 file1 file2
   3 files changed, 3 insertions(+)
   create mode 100644 file0
   create mode 100644 file1
   create mode 100644 file2

  $ git checkout -b head1
  Switched to a new branch 'head1'
  $ echo h1c1 > file1
  $ git add file1
  $ git commit -m h1c1
  [head1 ab003f0] h1c1
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ echo h2c2 > file1
  $ git add file1
  $ git commit -m h1c2
  [head1 cf9ad69] h1c2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git checkout master
  Switched to branch 'master'
  $ echo mc1 > file0
  $ git add file0
  $ git commit -m 'master c1'
  [master bcd2192] master c1
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ git checkout -b head2
  Switched to a new branch 'head2'
  $ echo h2c1 > file2
  $ git add file2
  $ git commit -m h2c1
  [head2 019d621] h2c1
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ echo h2c2 > file2
  $ git add file2
  $ git commit -m h2c2
  [head2 8de7644] h2c2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git checkout master
  Switched to branch 'master'
  $ echo mc2 > file0
  $ git add file0
  $ git commit -m 'master c2'
  [master 824ed6b] master c2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git log --graph --format=oneline --all
  * cf9ad694e235b1cdc386f05e7a177c364de926ee h1c2
  * ab003f0dcf722f60b12e1d88eb169294419afc1e h1c1
  | * 8de7644ef74338499cc06d361abcada458d63ae0 h2c2
  | * 019d621ccabb0fa19da01c2d2f6c6911f75fa80a h2c1
  | | * 824ed6bd9a20abbdfc2f30d51697fb38aaeed77f master c2
  | |/  
  | * bcd219215eeef8329b848347a4df596c97637c8d master c1
  |/  
  * 14ed61bb65666fab453c2c73779776b45a82ed1c add file0 file1 file2
  * a547cc07d30f025e022b27310c713705158c21b4 initial

  $ git for-each-ref
  cf9ad694e235b1cdc386f05e7a177c364de926ee commit	refs/heads/head1
  8de7644ef74338499cc06d361abcada458d63ae0 commit	refs/heads/head2
  824ed6bd9a20abbdfc2f30d51697fb38aaeed77f commit	refs/heads/master

  $ linearize-git --summary-prefix prefix: . heads/master
  linearizing 4 commits from heads/master (a547cc07d30f025e022b27310c713705158c21b4 to 824ed6bd9a20abbdfc2f30d51697fb38aaeed77f)
  1/4 a547cc07d30f025e022b27310c713705158c21b4 initial
  2/4 14ed61bb65666fab453c2c73779776b45a82ed1c add file0 file1 file2
  3/4 bcd219215eeef8329b848347a4df596c97637c8d master c1
  4/4 824ed6bd9a20abbdfc2f30d51697fb38aaeed77f master c2
  heads/master converted; original: 824ed6bd9a20abbdfc2f30d51697fb38aaeed77f; rewritten: a252594d0435ec401a688422fc9d5d8609411b31

  $ git log --graph --format=oneline convert/dest/heads/master
  * a252594d0435ec401a688422fc9d5d8609411b31 prefix: master c2
  * 43297b4d3719db354cd672eda3ccba002083fb51 prefix: master c1
  * adc692e75b22584d802c3e586719f16759126267 prefix: add file0 file1 file2
  * a8164f0194857c91f13cefc9ade0378488e89502 prefix: initial

  $ echo mc3 > file0
  $ git add file0
  $ git commit -m 'master c3'
  [master 9f1866b] master c3
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ git merge head1
  Merge made by the 'recursive' strategy.
   file1 | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ git merge head2
  Merge made by the 'recursive' strategy.
   file2 | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git log --graph --format=oneline
  *   c2aa3459b5fb3528e9808b6229a67165b4a3b565 Merge branch 'head2'
  |\  
  | * 8de7644ef74338499cc06d361abcada458d63ae0 h2c2
  | * 019d621ccabb0fa19da01c2d2f6c6911f75fa80a h2c1
  * |   8a64d1d9fabfd12eb7c8c2876b3a09b80a60657f Merge branch 'head1'
  |\ \  
  | * | cf9ad694e235b1cdc386f05e7a177c364de926ee h1c2
  | * | ab003f0dcf722f60b12e1d88eb169294419afc1e h1c1
  * | | 9f1866ba6011fb3621d68dcaa917d8d3044d7ccd master c3
  * | | 824ed6bd9a20abbdfc2f30d51697fb38aaeed77f master c2
  | |/  
  |/|   
  * | bcd219215eeef8329b848347a4df596c97637c8d master c1
  |/  
  * 14ed61bb65666fab453c2c73779776b45a82ed1c add file0 file1 file2
  * a547cc07d30f025e022b27310c713705158c21b4 initial

  $ linearize-git --summary-prefix prefix: . heads/master
  linearizing 3 commits from heads/master (9f1866ba6011fb3621d68dcaa917d8d3044d7ccd to c2aa3459b5fb3528e9808b6229a67165b4a3b565)
  1/3 9f1866ba6011fb3621d68dcaa917d8d3044d7ccd master c3
  2/3 8a64d1d9fabfd12eb7c8c2876b3a09b80a60657f Merge branch 'head1'
  3/3 c2aa3459b5fb3528e9808b6229a67165b4a3b565 Merge branch 'head2'
  heads/master converted; original: c2aa3459b5fb3528e9808b6229a67165b4a3b565; rewritten: 5d54e9062c565acba8fe3b7dda7e7fd1c29e550c

  $ git log --graph --format=oneline refs/convert/dest/heads/master
  * 5d54e9062c565acba8fe3b7dda7e7fd1c29e550c prefix: Merge branch 'head2'
  * b0923b63a71946878539e5a82b2430d2ececc0f2 prefix: Merge branch 'head1'
  * 7de4a0e3a1dec279df9f62590c2be67103957b97 prefix: master c3
  * a252594d0435ec401a688422fc9d5d8609411b31 prefix: master c2
  * 43297b4d3719db354cd672eda3ccba002083fb51 prefix: master c1
  * adc692e75b22584d802c3e586719f16759126267 prefix: add file0 file1 file2
  * a8164f0194857c91f13cefc9ade0378488e89502 prefix: initial
