#require mozreviewdocker

  $ . $TESTDIR/git/tests/helpers.sh
  $ gitmozreviewenv

  $ git -c fetch.prune=true clone hg::${MERCURIAL_URL}test-repo gitrepo
  Cloning into 'gitrepo'...
  $ cd gitrepo
  $ git mozreview configure --mercurial-url ${MERCURIAL_URL} --bugzilla-url ${BUGZILLA_URL}
  searching for appropriate review repository...
  using hg::http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  installing commit-msg hook

  $ bugzilla create-bug-range TestProduct TestComponent 3
  created bugs 1 to 3

Only have the base commit, which has no review identifier and is already on remote.
Should be a no-op push and should result in error

  $ git mozreview push
  abort: no commits pushed; `git checkout` to the commit to review
  [1]

Single commit on topic branch will submit 1 commit

  $ git checkout -b topic1
  Switched to a new branch 'topic1'
  $ echo topic1_1 > foo
  $ git commit --all -m 'Bug 1 - commit 1'
  [topic1 e42bea0] Bug 1 - commit 1
   1 file changed, 1 insertion(+)

  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog
  
  submitting 1 commits for review
  
  commit: e42bea0 Bug 1 - commit 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Additional commit on topic branch will submit 2 commits

  $ echo topic1_2 > foo
  $ git commit --all -m 'Bug 1 - commit 2'
  [topic1 d79633b] Bug 1 - commit 2
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog
  
  submitting 2 commits for review
  
  commit: e42bea0 Bug 1 - commit 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: d79633b Bug 1 - commit 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Topic branch on top of existing topic branch will submit all commits
(one day we may want to draw a boundary at ref changes as this fits the Git
branch-based development model a bit better)

  $ git checkout -b topic2
  Switched to a new branch 'topic2'
  $ echo topic2_1 > foo
  $ git commit --all -m 'Bug 1 - commit 3'
  [topic2 8de2e3a] Bug 1 - commit 3
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog
  
  submitting 3 commits for review
  
  commit: e42bea0 Bug 1 - commit 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: d79633b Bug 1 - commit 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  commit: 8de2e3a Bug 1 - commit 3
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Submitting commits referencing multiple bugs is refused

  $ git checkout topic1
  Switched to branch 'topic1'
  $ echo topic1_3 > foo
  $ git commit --all -m 'Bug 2 - Another bug'
  [topic1 d49c64f] Bug 2 - Another bug
   1 file changed, 1 insertion(+), 1 deletion(-)

  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  recorded push in pushlog
  
  error: cannot submit reviews referencing multiple bugs
  hint: limit reviewed commits by specifying a commit or revrange as an argument
  [1]

Specifying a refspec to review works

  $ git mozreview push HEAD~3..HEAD~1
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 2 commits for review
  
  commit: e42bea0 Bug 1 - commit 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: d79633b Bug 1 - commit 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)


Specifying a single commit on bottom of stack works

  $ git mozreview push e42bea0
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 1 commits for review
  
  commit: e42bea0 Bug 1 - commit 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Specifying a single commit in middle of stack works

  $ git mozreview push d79633b
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 1 commits for review
  
  commit: d79633b Bug 1 - commit 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Specifying a single commit on top of stack works

  $ echo topic1_4 > foo
  $ git commit --all -m 'Bug 2 - Commit 2'
  [topic1 fa60885] Bug 2 - Commit 2
   1 file changed, 1 insertion(+), 1 deletion(-)
  $ git mozreview push HEAD
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  recorded push in pushlog
  
  submitting 1 commits for review
  
  commit: fa60885 Bug 2 - Commit 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/6 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 5)

We don't review merge commits

  $ git checkout -b parent1 bb26661
  Switched to a new branch 'parent1'
  $ echo parent1 > bar
  $ git add bar
  $ git commit -m 'Bug 3 - Parent 1'
  [parent1 350abbd] Bug 3 - Parent 1
   1 file changed, 1 insertion(+)
   create mode 100644 bar
  $ git checkout -b parent2 bb26661
  Switched to a new branch 'parent2'
  $ echo parent2 > baz
  $ git add baz
  $ git commit -m 'Bug 3 - Parent 2'
  [parent2 6eddda2] Bug 3 - Parent 2
   1 file changed, 1 insertion(+)
   create mode 100644 baz
  $ git merge --commit -m 'Bug 3 - Merge' parent1
  Merge made by the 'recursive' strategy.
   bar | 1 +
   1 file changed, 1 insertion(+)
   create mode 100644 bar

  $ git mozreview push
  fatal: 'cinnabar' appears to be a git command, but we were not
  able to execute it. Maybe git-cinnabar is broken?
  abort: error performing cinnabar push; please report this bug
  [1]

Cleanup

  $ mozreview stop
  stopped 9 containers
