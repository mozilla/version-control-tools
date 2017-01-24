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
  $ GIT_AUTHOR_NAME='Old Author' GIT_AUTHOR_EMAIL=old-author@example.com GIT_COMMITTER_NAME='Old Committer' GIT_COMMITTER_EMAIL=old-committer@example.com git commit -m 1
  [master cb229ea] 1
   Author: Old Author <old-author@example.com>
   1 file changed, 1 insertion(+), 1 deletion(-)

Author map works

  $ cat > author_map << EOF
  > # This is a comment followed by an empty line
  > 
  > Old Author <old-author@example.com> = New Author <new-author@example.com>
  > Old Committer <old-committer@example.com> = New Committer <new-committer@example.com>
  > # This ia another comment
  > EOF

  $ linearize-git --author-map author_map . heads/master
  linearizing 2 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to cb229eaf293faecf0580d4b911000425a3338150)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 cb229eaf293faecf0580d4b911000425a3338150 1
  heads/master converted; original: cb229eaf293faecf0580d4b911000425a3338150; rewritten: cc01022a784bb7973b3ec8c5167c41302426286c

  $ git log convert/dest/heads/master
  commit cc01022a784bb7973b3ec8c5167c41302426286c
  Author: New Author <new-author@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      1
  
  commit dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial


  $ git cat-file -p convert/dest/heads/master
  tree a229c158b3d5560cc44ad3dec6ff5d13a47e11cf
  parent dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  author New Author <new-author@example.com> 0 +0000
  committer New Committer <new-committer@example.com> 0 +0000
  
  1
