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

--summary-prefix adds prefix to the summary line of commit message

  $ linearize-git --summary-prefix my-prefix: . heads/master
  linearizing 2 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to f3dcf0ea970616078b22c97ff104fa368b61973c)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 f3dcf0ea970616078b22c97ff104fa368b61973c commit 1
  heads/master converted; original: f3dcf0ea970616078b22c97ff104fa368b61973c; rewritten: 10874c20986a49df5dd96f35017858fc3e52fe70

  $ git cat-file -p 10874c20986a49df5dd96f35017858fc3e52fe70
  tree a229c158b3d5560cc44ad3dec6ff5d13a47e11cf
  parent e532d0c9cf2e5662401c8821f9eedb37356201f9
  author test <test@example.com> 0 +0000
  committer test <test@example.com> 0 +0000
  
  my-prefix: commit 1

  $ cd ..

Reviewable Markdown can be rewritten to a <key>: <URL> pattern

  $ git init grepo1
  Initialized empty Git repository in $TESTTMP/grepo1/.git/

  $ cd grepo1

  $ echo 0 > foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) dbd62b8] initial
   1 file changed, 1 insertion(+)
   create mode 100644 foo
  $ echo 1 > foo
  $ git add foo
  $ cat >> message << EOF
  > Auto merge of #14737 - UK992:package-prefs, r=Wafflespeanut
  > 
  > Package: Various improvements
  > 
  > Fixes https://github.com/servo/servo/issues/11966
  > Fixes https://github.com/servo/servo/issues/12707
  > 
  > <!-- Reviewable:start -->
  > ---
  > This change is [<img src="https://reviewable.io/review_button.svg" height="34" align="absmiddle" alt="Reviewable"/>](https://reviewable.io/reviews/servo/servo/14737)
  > <!-- Reviewable:end -->
  > EOF

  $ git commit -F message
  [master 9ccde32] Auto merge of #14737 - UK992:package-prefs, r=Wafflespeanut
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git branch master2 master

  $ linearize-git --reviewable-key Reviewable-URL . heads/master
  linearizing 2 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to 9ccde32cb7cc412d2c797a0fea52c258be9b76f2)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 9ccde32cb7cc412d2c797a0fea52c258be9b76f2 Auto merge of #14737 - UK992:package-prefs, r=Wafflespeanut
  heads/master converted; original: 9ccde32cb7cc412d2c797a0fea52c258be9b76f2; rewritten: 58b5ec5252ed2d3d8ab73d6abae4f6253b88674f

  $ git log convert/dest/heads/master
  commit 58b5ec5252ed2d3d8ab73d6abae4f6253b88674f
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Auto merge of #14737 - UK992:package-prefs, r=Wafflespeanut
      
      Package: Various improvements
      
      Fixes https://github.com/servo/servo/issues/11966
      Fixes https://github.com/servo/servo/issues/12707
      
      Reviewable-URL: https://reviewable.io/reviews/servo/servo/14737
  
  commit dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial

Reviewable.io Markdown can be removed

  $ linearize-git --remove-reviewable . heads/master2
  linearizing 2 commits from heads/master2 (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to 9ccde32cb7cc412d2c797a0fea52c258be9b76f2)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 9ccde32cb7cc412d2c797a0fea52c258be9b76f2 Auto merge of #14737 - UK992:package-prefs, r=Wafflespeanut
  heads/master2 converted; original: 9ccde32cb7cc412d2c797a0fea52c258be9b76f2; rewritten: e7fa11e1edfada45a007d36941b4d919f4b7fe5d

  $ git log convert/dest/heads/master2
  commit e7fa11e1edfada45a007d36941b4d919f4b7fe5d
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Auto merge of #14737 - UK992:package-prefs, r=Wafflespeanut
      
      Package: Various improvements
      
      Fixes https://github.com/servo/servo/issues/11966
      Fixes https://github.com/servo/servo/issues/12707
  
  commit dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial

  $ cd ..

GitHub pull request commit message rewriting works

  $ git init grepo2
  Initialized empty Git repository in $TESTTMP/grepo2/.git/
  $ cd grepo2
  $ echo 0 > foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) dbd62b8] initial
   1 file changed, 1 insertion(+)
   create mode 100644 foo

  $ echo 1 > foo
  $ git add foo

First non-blank line is the summary line

  $ cat > message << EOF
  > Merge pull request #376 from servo/foo-feature
  > 
  > Removed reference to cairo from servo-gfx/font.rs
  > 
  > More data below
  > EOF

  $ git commit -F message
  [master 026e845] Merge pull request #376 from servo/foo-feature
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ echo 2 > foo
  $ git add foo
  $ cat > message << EOF
  > Merge pull request #653 from foo/bar
  > No blank line after summary
  > 
  > More content here
  > EOF
  $ git commit -F message
  [master 2e52fe5] Merge pull request #653 from foo/bar No blank line after summary
   1 file changed, 1 insertion(+), 1 deletion(-)

Servo style commit message syntax rewriting works

  $ echo 3 > foo
  $ git add foo
  $ cat > message << EOF
  > Auto merge of #6532 - servo/bar-feature, r=gps
  > 
  > This is the PR summary line
  > 
  > Extra content here
  > EOF
  $ git commit -F message
  [master fa522c7] Auto merge of #6532 - servo/bar-feature, r=gps
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ echo 4 > foo
  $ git add foo
  $ cat > message << EOF
  > auto merge of #4690 : indygreg/servo/some-feature, r=bholley
  > 
  > Summary line w/o PR JSON
  > EOF
  $ git commit -F message
  [master cf1c79b] auto merge of #4690 : indygreg/servo/some-feature, r=bholley
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ echo 5 > foo
  $ git add foo
  $ cat > message << EOF
  > Auto merge of #5700 - Ms2ger:content, r=jdm
  > 
  > 
  > 
  > <!-- Reviewable:start -->
  > [<img src="https://reviewable.io/review_button.png" height=40 alt="Review on Reviewable"/>](https://reviewable.io/reviews/servo/servo/5700)
  > <!-- Reviewable:end -->
  > EOF
  $ git commit -F message
  [master a7332b8] Auto merge of #5700 - Ms2ger:content, r=jdm
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ linearize-git --normalize-github-merge-message --remove-reviewable . heads/master
  linearizing 6 commits from heads/master (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to a7332b8424dc931df611b8feab5fa6840218bfa1)
  1/6 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/6 026e845f3f1293fb53ea2ee98cbc349120993c7c Merge pull request #376 from servo/foo-feature
  3/6 2e52fe53a63dc972ef737702f0467ea0575d0392 Merge pull request #653 from foo/bar
  4/6 fa522c79808c18641e57fff1e3a7d67ae802fa04 Auto merge of #6532 - servo/bar-feature, r=gps
  5/6 cf1c79b916bc61fa77a215acb13f00c770d2ac9e auto merge of #4690 : indygreg/servo/some-feature, r=bholley
  6/6 a7332b8424dc931df611b8feab5fa6840218bfa1 Auto merge of #5700 - Ms2ger:content, r=jdm
  heads/master converted; original: a7332b8424dc931df611b8feab5fa6840218bfa1; rewritten: 804b27caa81d7ac94b2ad48e23f1b152c21c5490

  $ git log refs/convert/dest/heads/master
  commit 804b27caa81d7ac94b2ad48e23f1b152c21c5490
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge #5700 (from Ms2ger:content); r=jdm
  
  commit 1924605259679ed7f3115d6d316ecf0f5664d286
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge #4690 - Summary line w/o PR JSON (from indygreg/servo/some-feature); r=bholley
  
  commit a41d8edf9850a8d7372a9cbe0b544ea552752432
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge #6532 - This is the PR summary line (from servo/bar-feature); r=gps
      
      Extra content here
  
  commit 97edfbc3c88a6fd32e67b88428384e700eda0cfb
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge #653 - No blank line after summary (from foo:bar)
      
      More content here
  
  commit e852a645a35166cfe99ed9457a63fd0a9c2d0f38
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Merge #376 - Removed reference to cairo from servo-gfx/font.rs (from servo:foo-feature)
      
      More data below
  
  commit dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial
