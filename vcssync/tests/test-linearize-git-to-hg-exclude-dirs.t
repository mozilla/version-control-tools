#require hg41+

  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ standardgitrepo grepo > /dev/null 2>&1
  $ linearize-git-to-hg file://$TESTTMP/grepo master grepo-source grepo-dest > /dev/null 2>&1

Directories can be excluded when linearizing

  $ cd grepo
  $ mkdir dir1
  $ echo 0 > dir1/dir1_file0
  $ echo 1 > dir1/dir1_file1
  $ git add --all
  $ git commit -m ignore > /dev/null
  $ cd ..

  $ linearize-git-to-hg file://$TESTTMP/grepo master grepo-source grepo-dest --exclude-dir dir1
  From file://$TESTTMP/grepo
     a447b9b..ad3f6b5  master     -> master
  linearizing 1 commits from heads/master (ad3f6b56f7320d386c2ce2574b0573d1ad88773b to ad3f6b56f7320d386c2ce2574b0573d1ad88773b)
  1/1 ad3f6b56f7320d386c2ce2574b0573d1ad88773b ignore
  dropping ad3f6b56f7320d386c2ce2574b0573d1ad88773b because no tree changes
  0 commits from heads/master converted; original: ad3f6b56f7320d386c2ce2574b0573d1ad88773b; rewritten: aea30981234cf6848489e0ccf541fbf902b27aca
  all Git commits have already been converted; not doing anything
  $ cd grepo-dest
  $ hg files -r tip
  bar
  file0-copied-with-move
  file0-copy0
  file0-copy1
  file0-copy2
  file0-moved-with-copy
  file1
  file1-20
  file1-50
  file1-80
  foo
  $ cd ..

--exclude-dir works multiple times

  $ cd grepo
  $ mkdir dir2
  $ echo 0 > dir2/file0
  $ git add --all
  $ git commit -m ignore-multi > /dev/null
  $ cd ..

  $ linearize-git-to-hg file://$TESTTMP/grepo master grepo-source grepo-dest --exclude-dir dir1 --exclude-dir dir2
  From file://$TESTTMP/grepo
     ad3f6b5..04ac57d  master     -> master
  linearizing 1 commits from heads/master (04ac57d95ed6dd954cceead6f95fcbb047c80760 to 04ac57d95ed6dd954cceead6f95fcbb047c80760)
  1/1 04ac57d95ed6dd954cceead6f95fcbb047c80760 ignore-multi
  dropping 04ac57d95ed6dd954cceead6f95fcbb047c80760 because no tree changes
  0 commits from heads/master converted; original: 04ac57d95ed6dd954cceead6f95fcbb047c80760; rewritten: aea30981234cf6848489e0ccf541fbf902b27aca
  all Git commits have already been converted; not doing anything
  $ cd grepo-dest
  $ hg files -r tip
  bar
  file0-copied-with-move
  file0-copy0
  file0-copy1
  file0-copy2
  file0-moved-with-copy
  file1
  file1-20
  file1-50
  file1-80
  foo
  $ cd ..

Excluding an intermediate directory works  --exclude-dir ignore2/subdir0

  $ cd grepo
  $ mkdir -p dir3/subdir0
  $ echo 0 > dir3/file0
  $ echo 1 > dir3/subdir0/file1
  $ git add --all
  $ git commit -m ignore-multi > /dev/null
  $ cd ..

  $ linearize-git-to-hg file://$TESTTMP/grepo master grepo-source grepo-dest --exclude-dir dir1 --exclude-dir dir2 --exclude-dir dir3/subdir0
  From file://$TESTTMP/grepo
     04ac57d..36d2de4  master     -> master
  linearizing 1 commits from heads/master (36d2de48325568c9bce9ff67d66ed6aca4c9b2e9 to 36d2de48325568c9bce9ff67d66ed6aca4c9b2e9)
  1/1 36d2de48325568c9bce9ff67d66ed6aca4c9b2e9 ignore-multi
  1 commits from heads/master converted; original: 36d2de48325568c9bce9ff67d66ed6aca4c9b2e9; rewritten: 95c25188f219f5c68497863faba183fbbbbfae04
  converting 1 Git commits
  scanning source...
  sorting...
  converting...
  0 ignore-multi
  1 Git commits converted to Mercurial; previous tip: 10:7d80acaa161029d9e746e3125e7cc0916406403f; current tip: 11:4c82e4e6f1944acf408939cee63fc5c078de73df
  $ cd grepo-dest
  $ hg files -r tip
  bar
  dir3/file0
  file0-copied-with-move
  file0-copy0
  file0-copy1
  file0-copy2
  file0-moved-with-copy
  file1
  file1-20
  file1-50
  file1-80
  foo
  $ cd ..
