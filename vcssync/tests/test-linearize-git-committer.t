  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ export GIT_AUTHOR_NAME='Git Author'
  $ export GIT_AUTHOR_EMAIL='author@example.com'
  $ export GIT_COMMITTER_NAME='Git Committer'
  $ export GIT_COMMITTER_EMAIL='committer@example.com>'
  $ export GIT_COMMITTER_DATE='Fri Jan 6 00:00:00 2017 +0000'

  $ git init grepo0
  Initialized empty Git repository in $TESTTMP/grepo0/.git/

  $ cd grepo0

  $ echo 0 > foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) 81ceece] initial
   Author: Git Author <author@example.com>
   1 file changed, 1 insertion(+)
   create mode 100644 foo
  $ git branch keep
  $ git branch use-author
  $ git branch use-committer

Git committer should be retained by default

  $ linearize-git . heads/master
  linearizing 1 commits from heads/master (81ceece45bfdbe831a28eb6b90d196aea1330184 to 81ceece45bfdbe831a28eb6b90d196aea1330184)
  1/1 81ceece45bfdbe831a28eb6b90d196aea1330184 initial
  heads/master converted; original: 81ceece45bfdbe831a28eb6b90d196aea1330184; rewritten: 81ceece45bfdbe831a28eb6b90d196aea1330184

  $ git cat-file -p refs/convert/dest/heads/master
  tree 2d2675b9e90bde3e722e6ef55faee52aec2e3857
  author Git Author <author@example.com> 0 +0000
  committer Git Committer <committer@example.com> 1483660800 +0000
  
  initial

--committer-action keep is the default behavior

  $ linearize-git --committer-action keep . heads/keep
  linearizing 1 commits from heads/keep (81ceece45bfdbe831a28eb6b90d196aea1330184 to 81ceece45bfdbe831a28eb6b90d196aea1330184)
  1/1 81ceece45bfdbe831a28eb6b90d196aea1330184 initial
  heads/keep converted; original: 81ceece45bfdbe831a28eb6b90d196aea1330184; rewritten: 81ceece45bfdbe831a28eb6b90d196aea1330184

  $ git cat-file -p refs/convert/dest/heads/keep
  tree 2d2675b9e90bde3e722e6ef55faee52aec2e3857
  author Git Author <author@example.com> 0 +0000
  committer Git Committer <committer@example.com> 1483660800 +0000
  
  initial

use-author copies author to committer

  $ linearize-git --committer-action use-author . heads/use-author
  linearizing 1 commits from heads/use-author (81ceece45bfdbe831a28eb6b90d196aea1330184 to 81ceece45bfdbe831a28eb6b90d196aea1330184)
  1/1 81ceece45bfdbe831a28eb6b90d196aea1330184 initial
  heads/use-author converted; original: 81ceece45bfdbe831a28eb6b90d196aea1330184; rewritten: 42591cc3c328b9e9c0ee9ae6e4573894b17ba691

  $ git cat-file -p refs/convert/dest/heads/use-author
  tree 2d2675b9e90bde3e722e6ef55faee52aec2e3857
  author Git Author <author@example.com> 0 +0000
  committer Git Author <author@example.com> 0 +0000
  
  initial

use-committer copies committer to author

  $ linearize-git --committer-action use-committer . heads/use-committer
  linearizing 1 commits from heads/use-committer (81ceece45bfdbe831a28eb6b90d196aea1330184 to 81ceece45bfdbe831a28eb6b90d196aea1330184)
  1/1 81ceece45bfdbe831a28eb6b90d196aea1330184 initial
  heads/use-committer converted; original: 81ceece45bfdbe831a28eb6b90d196aea1330184; rewritten: 610b4fec36ab4c55172fa95cfa9c462323ad335f

  $ git cat-file -p refs/convert/dest/heads/use-committer
  tree 2d2675b9e90bde3e722e6ef55faee52aec2e3857
  author Git Committer <committer@example.com> 1483660800 +0000
  committer Git Committer <committer@example.com> 1483660800 +0000
  
  initial
