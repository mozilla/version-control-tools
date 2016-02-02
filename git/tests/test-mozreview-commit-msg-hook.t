  $ . $TESTDIR/git/tests/helpers.sh

  $ git init testrepo
  Initialized empty Git repository in $TESTTMP/testrepo/.git/
  $ cd testrepo
  $ touch foo
  $ git add foo
  $ git commit -m initial
  [master (root-commit) a547cc0] initial
   1 file changed, 0 insertions(+), 0 deletions(-)
   create mode 100644 foo

Install the commit-msg hook

  $ cp $TESTDIR/git/hooks/commit-msg-mozreview .git/hooks/commit-msg
  $ cat > .git/fakeids << EOF
  > 0
  > EOF
  $ export FAKEIDPATH=.git/fakeids

MozReview-Commit-ID should be added to bottom of commit message

  $ echo 1 > foo
  $ git commit --all -m 'Bug 1 - Commit 1'
  [master 4802c89] Bug 1 - Commit 1
   1 file changed, 1 insertion(+)

  $ git log
  commit 4802c898bf197f38b34a252101238a7ba9136e54
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Bug 1 - Commit 1
      
      MozReview-Commit-ID: 124Bxg
  
  commit a547cc07d30f025e022b27310c713705158c21b4
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial

Amending commit should not alter commit message

  $ echo 2 > foo
  $ git commit --all -m 'Bug 1 - Commit 2'
  [master 85b2133] Bug 1 - Commit 2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git log
  commit 85b2133993d3f60ac11bea2271b888c32d968c27
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Bug 1 - Commit 2
      
      MozReview-Commit-ID: 5ijR9k
  
  commit 4802c898bf197f38b34a252101238a7ba9136e54
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Bug 1 - Commit 1
      
      MozReview-Commit-ID: 124Bxg
  
  commit a547cc07d30f025e022b27310c713705158c21b4
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      initial

Commit ID should not be added when creating a special fixup or squash commit

  $ echo 3 > foo
  $ git commit --all --fixup HEAD
  [master 2d84a9d] fixup! Bug 1 - Commit 2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git log -n 1 HEAD
  commit 2d84a9dcf904c5e7a3b589feb0ab7e0974dd3beb
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      fixup! Bug 1 - Commit 2

  $ echo 4 > foo
  $ git commit --all --squash HEAD -m 'commit 4'
  [master 8bf68fe] squash! fixup! Bug 1 - Commit 2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git log -n 1 HEAD
  commit 8bf68fef23885be4ca7c48615707fb922a4b7868
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      squash! fixup! Bug 1 - Commit 2
      
      commit 4

Commit ID isn't updated when already present

  $ git checkout -b no-rewrite a547cc07
  Switched to a new branch 'no-rewrite'

  $ cat > message << EOF
  > Bug 2 - Testing existing commit ID
  > 
  > MozReview-Commit-ID: abc123
  > EOF

  $ echo 5 > foo
  $ git add foo
  $ git commit -F message
  [no-rewrite 9fd2ae9] Bug 2 - Testing existing commit ID
   1 file changed, 1 insertion(+)

  $ git log -n 1 HEAD
  commit 9fd2ae90647d151458e387807edb54f0ecbe9359
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Bug 2 - Testing existing commit ID
      
      MozReview-Commit-ID: abc123

MozReview-Commit-ID is not on the final line

  $ echo 6 > foo
  $ git add foo
  $ cat > message << EOF
  > Bug 2 - Not on final line
  > 
  > Some other text.
  > 
  > MozReview-Commit-ID: def456
  > Signed-Off-By: gps
  > EOF

  $ git commit -F message
  [no-rewrite ad33368] Bug 2 - Not on final line
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git log -n 1 HEAD
  commit ad3336842ac595b795cb178bcb70b75f72fe6e79
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Bug 2 - Not on final line
      
      Some other text.
      
      MozReview-Commit-ID: def456
      Signed-Off-By: gps

No extra line is inserted after existing key: value metadata

  $ git checkout -b no-buffer-line a547cc07
  Switched to a new branch 'no-buffer-line'
  $ echo 2 > foo
  $ git add foo
  $ cat > message << EOF
  > Bug 3 - No buffer
  > 
  > Extra content.
  > 
  > Signed-Off-By: gps
  > EOF

  $ git commit -F message
  [no-buffer-line 259357a] Bug 3 - No buffer
   1 file changed, 1 insertion(+)

  $ git log -n 1 HEAD
  commit 259357a9f090472fac8553dbc2b74ce85c108a65
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Bug 3 - No buffer
      
      Extra content.
      
      Signed-Off-By: gps
      MozReview-Commit-ID: APOgLo

Inline diff in commit message is ignored

  $ git checkout -b inline-diff a547cc07
  Switched to a new branch 'inline-diff'
  $ echo inline-diff > foo
  $ git add foo
  $ cat > message << EOF
  > Bug 4 - Inline diff
  > 
  > Extra content.
  > EOF
  $ git commit -v -F message
  [inline-diff 21682a5] Bug 4 - Inline diff
   1 file changed, 1 insertion(+)

  $ git log -n 1 HEAD
  commit 21682a57a7138baa766f39f4c2617968946ae60c
  Author: test <test@example.com>
  Date:   Thu Jan 1 00:00:00 1970 +0000
  
      Bug 4 - Inline diff
      
      Extra content.
      
      MozReview-Commit-ID: F63vXs
