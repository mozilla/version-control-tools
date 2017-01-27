  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ git init repo0
  Initialized empty Git repository in $TESTTMP/repo0/.git/

  $ cd repo0
  $ touch file0
  $ git add file0
  $ git commit -m initial
  [master (root-commit) 9a1c63e] initial
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 file0

  $ mkdir dir0 dir1
  $ touch dir0/file0 dir1/file0
  $ git add dir0 dir1
  $ git commit -m 'add dir0/file0 and dir1/file0'
  [master 91896bd] add dir0/file0 and dir1/file0
   2 files changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir0/file0
   create mode 100644 dir1/file0
  $ git branch before-dir1
  $ touch dir1/file1
  $ git add dir1/file1
  $ git commit -m 'add dir1/file1'
  [master 3219fc6] add dir1/file1
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir1/file1
  $ touch dir1/file2
  $ git add dir1/file2
  $ git commit -m 'add dir1/file2'
  [master a870890] add dir1/file2
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir1/file2
  $ touch dir0/file1
  $ git add dir0/file1
  $ git commit -m 'add dir0/file1'
  [master 9826ff3] add dir0/file1
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 dir0/file1

Linearizing master should drop commits only touching dir1

  $ linearize-git --exclude-dir dir1 . heads/master
  linearizing 5 commits from heads/master (9a1c63edf1b4ddedd8b4c6ead8e7d9d613a40c4b to 9826ff342e616ccbb358c7d6ea25c6d695a74a23)
  1/5 9a1c63edf1b4ddedd8b4c6ead8e7d9d613a40c4b initial
  2/5 91896bd2582da05399b9f2203676701b5ca7c86f add dir0/file0 and dir1/file0
  3/5 3219fc60822be2815a418dac5a355551aa79b60b add dir1/file1
  dropping 3219fc60822be2815a418dac5a355551aa79b60b because no tree changes
  4/5 a87089085cdd007a4b176ae84dad07af750e0615 add dir1/file2
  dropping a87089085cdd007a4b176ae84dad07af750e0615 because no tree changes
  5/5 9826ff342e616ccbb358c7d6ea25c6d695a74a23 add dir0/file1
  3 commits from heads/master converted; original: 9826ff342e616ccbb358c7d6ea25c6d695a74a23; rewritten: aba6d76d367154ca87f9b5b177852f0a85f50b65

Test incremental conversion where empty commits are on edges

  $ linearize-git --exclude-dir dir1 . heads/before-dir1
  linearizing 2 commits from heads/before-dir1 (9a1c63edf1b4ddedd8b4c6ead8e7d9d613a40c4b to 91896bd2582da05399b9f2203676701b5ca7c86f)
  1/2 9a1c63edf1b4ddedd8b4c6ead8e7d9d613a40c4b initial
  2/2 91896bd2582da05399b9f2203676701b5ca7c86f add dir0/file0 and dir1/file0
  2 commits from heads/before-dir1 converted; original: 91896bd2582da05399b9f2203676701b5ca7c86f; rewritten: 66547f310f848f1024fbda495dafebd3c6c347f9

  $ git checkout before-dir1
  Switched to branch 'before-dir1'
  $ git reset --hard 3219fc60822be2815a418dac5a355551aa79b60b
  HEAD is now at 3219fc6 add dir1/file1
  $ linearize-git --exclude-dir dir1 . heads/before-dir1
  linearizing 1 commits from heads/before-dir1 (3219fc60822be2815a418dac5a355551aa79b60b to 3219fc60822be2815a418dac5a355551aa79b60b)
  1/1 3219fc60822be2815a418dac5a355551aa79b60b add dir1/file1
  dropping 3219fc60822be2815a418dac5a355551aa79b60b because no tree changes
  0 commits from heads/before-dir1 converted; original: 3219fc60822be2815a418dac5a355551aa79b60b; rewritten: 66547f310f848f1024fbda495dafebd3c6c347f9

  $ git reset --hard a87089085cdd007a4b176ae84dad07af750e0615
  HEAD is now at a870890 add dir1/file2
  $ linearize-git --exclude-dir dir1 . heads/before-dir1
  linearizing 1 commits from heads/before-dir1 (a87089085cdd007a4b176ae84dad07af750e0615 to a87089085cdd007a4b176ae84dad07af750e0615)
  1/1 a87089085cdd007a4b176ae84dad07af750e0615 add dir1/file2
  dropping a87089085cdd007a4b176ae84dad07af750e0615 because no tree changes
  0 commits from heads/before-dir1 converted; original: a87089085cdd007a4b176ae84dad07af750e0615; rewritten: 66547f310f848f1024fbda495dafebd3c6c347f9

  $ git reset --hard 9826ff342e616ccbb358c7d6ea25c6d695a74a23
  HEAD is now at 9826ff3 add dir0/file1
  $ linearize-git --exclude-dir dir1 . heads/before-dir1
  linearizing 1 commits from heads/before-dir1 (9826ff342e616ccbb358c7d6ea25c6d695a74a23 to 9826ff342e616ccbb358c7d6ea25c6d695a74a23)
  1/1 9826ff342e616ccbb358c7d6ea25c6d695a74a23 add dir0/file1
  1 commits from heads/before-dir1 converted; original: 9826ff342e616ccbb358c7d6ea25c6d695a74a23; rewritten: aba6d76d367154ca87f9b5b177852f0a85f50b65

Converted commit SHA-1 for master should align with incremental result

  $ git for-each-ref
  aba6d76d367154ca87f9b5b177852f0a85f50b65 commit	refs/convert/dest/heads/before-dir1
  aba6d76d367154ca87f9b5b177852f0a85f50b65 commit	refs/convert/dest/heads/master
  9826ff342e616ccbb358c7d6ea25c6d695a74a23 commit	refs/convert/source/heads/before-dir1
  9826ff342e616ccbb358c7d6ea25c6d695a74a23 commit	refs/convert/source/heads/master
  9826ff342e616ccbb358c7d6ea25c6d695a74a23 commit	refs/heads/before-dir1
  9826ff342e616ccbb358c7d6ea25c6d695a74a23 commit	refs/heads/master
