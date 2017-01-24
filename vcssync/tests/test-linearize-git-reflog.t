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

Need to change the committer date because reflogs rely on that time

  $ export GIT_COMMITTER_DATE='Fri Jan 6 00:00:00 2017 +0000'

  $ linearize-git --summary-prefix prefix: . heads/master
  linearizing 1 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf)
  1/1 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  heads/master converted; original: dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf; rewritten: 6f15a738f983e864bdfac5088fcb9c4c0e339757

refs tracking converted commits have a reflog entry

  $ git reflog show convert/source/heads/master
  dbd62b8 convert/source/heads/master@{0}: linearize heads/master

  $ git reflog show convert/dest/heads/master
  6f15a73 convert/dest/heads/master@{0}: linearize heads/master

Performing an incremental conversion will create a new reflog entry

  $ echo 1 > foo
  $ git add foo
  $ git commit -m initial
  [master ccdbd02] initial
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ export GIT_COMMITTER_DATE='Fri Jan 6 00:00:01 2017 +0000'

  $ linearize-git --summary-prefix prefix: . heads/master
  linearizing 1 commits from heads/master (ccdbd027bb70f567e4e21296450e0c991ee52d4b to ccdbd027bb70f567e4e21296450e0c991ee52d4b)
  1/1 ccdbd027bb70f567e4e21296450e0c991ee52d4b initial
  heads/master converted; original: ccdbd027bb70f567e4e21296450e0c991ee52d4b; rewritten: e800cfd3c722caab882652b26f98a9e568582a60

  $ git reflog show convert/source/heads/master
  ccdbd02 convert/source/heads/master@{0}: linearize heads/master
  dbd62b8 convert/source/heads/master@{1}: linearize heads/master

  $ git reflog show convert/dest/heads/master
  e800cfd convert/dest/heads/master@{0}: linearize heads/master
  6f15a73 convert/dest/heads/master@{1}: linearize heads/master
