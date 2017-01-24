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
  $ echo 1 > foo
  $ git add foo
  $ git commit -m 'commit 1'
  [master f3dcf0e] commit 1
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ echo 2 > foo
  $ git add foo
  $ git commit -m 'commit 2'
  [master 2a57f45] commit 2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ linearize-git . heads/master
  linearizing 3 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to 2a57f453609d9dffe0dad9a0544b792a09d4b234)
  1/3 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/3 f3dcf0ea970616078b22c97ff104fa368b61973c commit 1
  3/3 2a57f453609d9dffe0dad9a0544b792a09d4b234 commit 2
  heads/master converted; original: 2a57f453609d9dffe0dad9a0544b792a09d4b234; rewritten: 2a57f453609d9dffe0dad9a0544b792a09d4b234

Simulate a force push by doing a hard reset + new commit

  $ git reset --hard f3dcf0ea970616078b22c97ff104fa368b61973c
  HEAD is now at f3dcf0e commit 1
  $ echo 2.new > foo
  $ git add foo
  $ git commit -m 'commit 3 (reset)'
  [master 280dddb] commit 3 (reset)
   1 file changed, 1 insertion(+), 1 deletion(-)

Attempting an incremental conversion that isn't a fast forward will result in
error.

  $ linearize-git . heads/master
  abort: source commit 2a57f453609d9dffe0dad9a0544b792a09d4b234 not found in ref heads/master; refusing to convert non-fast-forward history

And again on HEAD~2

  $ git reset --hard dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  HEAD is now at dbd62b8 initial
  $ echo 1.new > foo
  $ git add foo
  $ git commit -m 'commit 2 (reset)'
  [master ea5210e] commit 2 (reset)
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ linearize-git . heads/master
  abort: source commit 2a57f453609d9dffe0dad9a0544b792a09d4b234 not found in ref heads/master; refusing to convert non-fast-forward history

Resetting back to original will recover

  $ git reset --hard 2a57f453609d9dffe0dad9a0544b792a09d4b234
  HEAD is now at 2a57f45 commit 2
  $ echo 3 > foo
  $ git add foo
  $ git commit -m 'commit 3'
  [master 10b4510] commit 3
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ linearize-git . heads/master
  linearizing 1 commits from heads/master (10b45106160cb14fd510875c844f38ea26b559c6 to 10b45106160cb14fd510875c844f38ea26b559c6)
  1/1 10b45106160cb14fd510875c844f38ea26b559c6 commit 3
  heads/master converted; original: 10b45106160cb14fd510875c844f38ea26b559c6; rewritten: 10b45106160cb14fd510875c844f38ea26b559c6
