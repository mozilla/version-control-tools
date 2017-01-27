  $ . $TESTDIR/vcssync/tests/helpers.sh

Create a Git repo with a simple merge

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
  $ cat >> message << EOF
  > commit 1
  > 
  > Reviewable-URL: https://example.com/foo
  > EOF
  $ git commit -F message
  [master 4064f3a] commit 1
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ git branch master2
  $ git branch master3
  $ git branch master4

Source repo annotations work

  $ linearize-git --source-repo https://github.com/example/repo.git --source-repo-key Source-Repo . heads/master2
  linearizing 2 commits from heads/master2 (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to 4064f3a8845ed27962b26096cfae39610ea97c8e)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 4064f3a8845ed27962b26096cfae39610ea97c8e commit 1
  2 commits from heads/master2 converted; original: 4064f3a8845ed27962b26096cfae39610ea97c8e; rewritten: 08225afa188929f3b1b5b06d2dff1e0a6dbbd707

  $ git cat-file -p 08225afa188929f3b1b5b06d2dff1e0a6dbbd707
  tree a229c158b3d5560cc44ad3dec6ff5d13a47e11cf
  parent c7a2854e7d8d1f3e6b1abc8bd7cf8a6a1a225f9f
  author test <test@example.com> 0 +0000
  committer test <test@example.com> 0 +0000
  
  commit 1
  
  Reviewable-URL: https://example.com/foo
  Source-Repo: https://github.com/example/repo.git

  $ linearize-git --source-revision-key Source-Revision . heads/master3
  linearizing 2 commits from heads/master3 (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to 4064f3a8845ed27962b26096cfae39610ea97c8e)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 4064f3a8845ed27962b26096cfae39610ea97c8e commit 1
  2 commits from heads/master3 converted; original: 4064f3a8845ed27962b26096cfae39610ea97c8e; rewritten: f7fabf46f67fae5f49e2776b72307a7d17cd560f

  $ git cat-file -p f7fabf46f67fae5f49e2776b72307a7d17cd560f
  tree a229c158b3d5560cc44ad3dec6ff5d13a47e11cf
  parent 1c8e8b4b1c0c0eca6b0452241f05fe983c6f3b52
  author test <test@example.com> 0 +0000
  committer test <test@example.com> 0 +0000
  
  commit 1
  
  Reviewable-URL: https://example.com/foo
  Source-Revision: 4064f3a8845ed27962b26096cfae39610ea97c8e

  $ linearize-git --source-repo https://github.com/example/repo.git --source-repo-key Source-Repo --source-revision-key Source-Revision . heads/master4
  linearizing 2 commits from heads/master4 (dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf to 4064f3a8845ed27962b26096cfae39610ea97c8e)
  1/2 dbd62b82aaf0a7a05665d9455a9b4d490d52ddaf initial
  2/2 4064f3a8845ed27962b26096cfae39610ea97c8e commit 1
  2 commits from heads/master4 converted; original: 4064f3a8845ed27962b26096cfae39610ea97c8e; rewritten: e39b36eab045450d8cf25e77532aa5c062da792d

  $ git cat-file -p e39b36eab045450d8cf25e77532aa5c062da792d
  tree a229c158b3d5560cc44ad3dec6ff5d13a47e11cf
  parent d59910e04b7469ebc5f93299632836c79c5a0aff
  author test <test@example.com> 0 +0000
  committer test <test@example.com> 0 +0000
  
  commit 1
  
  Reviewable-URL: https://example.com/foo
  Source-Repo: https://github.com/example/repo.git
  Source-Revision: 4064f3a8845ed27962b26096cfae39610ea97c8e
