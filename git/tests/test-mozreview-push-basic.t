#require mozreviewdocker

  $ . $TESTDIR/git/tests/helpers.sh
  $ gitmozreviewenv

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ git -c fetch.prune=true clone hg::${MERCURIAL_URL}test-repo gitrepo
  Cloning into 'gitrepo'...
  $ cd gitrepo

Using mozreview push before configure complains

  $ git mozreview push
  abort: configuration needed; run `git mozreview configure`
  [1]

  $ git mozreview configure --mercurial-url ${MERCURIAL_URL} --bugzilla-url ${BUGZILLA_URL}
  searching for appropriate review repository...
  using hg::http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  installing commit-msg hook

Create some commits to review

  $ git checkout -b my-topic
  Switched to a new branch 'my-topic'
  $ echo 1 > foo
  $ git commit --all -m 'Bug 1 - Foo 1'
  [my-topic 4ba654c] Bug 1 - Foo 1
   1 file changed, 1 insertion(+)
  $ echo 2 > foo
  $ git commit --all -m 'Bug 1 - Foo 2'
  [my-topic f6c6fd8] Bug 1 - Foo 2
   1 file changed, 1 insertion(+), 1 deletion(-)

mozreview push will submit for code review

  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  recorded push in pushlog
  
  submitting 2 commits for review
  
  commit: 4ba654c Bug 1 - Foo 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  commit: f6c6fd8 Bug 1 - Foo 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Reviews should be published and Bugzilla attachments should be present

  $ rbmanage dumpreview 1
  id: 1
  status: pending
  public: true
  bugs:
  - '1'
  commit: bz://1/mynick
  submitter: default+5
  summary: bz://1/mynick
  description: This is the parent review request
  target_people: []
  extra_data:
    calculated_trophies: true
    p2rb.reviewer_map: '{}'
  commit_extra_data:
    p2rb: true
    p2rb.base_commit: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c
    p2rb.commits: '[["f7ac6c88ab11801e6f7e22b2de292ed6bd1932a4", 2], ["fc8ecbaed44d222dcc9735a5019f21ca00e003b4",
      3]]'
    p2rb.discard_on_publish_rids: '[]'
    p2rb.first_public_ancestor: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c
    p2rb.has_commit_message_filediff: true
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: true
    p2rb.unpublished_rids: '[]'
  diffs:
  - id: 1
    revision: 1
    base_commit_id: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -0,0 +1,1 @@'
    - '+2'
    - ''
  approved: false
  approval_failure: Commit f7ac6c88ab11801e6f7e22b2de292ed6bd1932a4 is not approved.

  $ rbmanage dumpreview 2
  id: 2
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - Foo 1
  description:
  - Bug 1 - Foo 1
  - ''
  - 'MozReview-Commit-ID: 124Bxg'
  target_people: []
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test <test@example.com>
    p2rb.commit_id: f7ac6c88ab11801e6f7e22b2de292ed6bd1932a4
    p2rb.commit_message_filediff_ids: '{"1": 2}'
    p2rb.commit_message_filename: commit-message-96ee1
    p2rb.first_public_ancestor: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 3
    revision: 1
    base_commit_id: 96ee1d7354c4ad7372047672c36a1f561e3a6a4c
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -0,0 +1,1 @@'
    - '+1'
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

  $ bugzilla dump-bug 1
  Bug 1:
    attachments:
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header
      description: Bug 1 - Foo 1
      file_name: reviewboard-2-url.txt
      flags: []
      id: 1
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Foo 1
    - attacher: default@example.com
      content_type: text/x-review-board-request
      data: http://$DOCKER_HOSTNAME:$HGPORT1/r/3/diff/#index_header
      description: Bug 1 - Foo 2
      file_name: reviewboard-3-url.txt
      flags: []
      id: 2
      is_obsolete: false
      is_patch: false
      summary: Bug 1 - Foo 2
    blocks: []
    cc: []
    comments:
    - author: default@example.com
      id: 1
      tags: []
      text: ''
    - author: default@example.com
      id: 2
      tags:
      - mozreview-request
      text:
      - Created attachment 1
      - Bug 1 - Foo 1
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/2/'
    - author: default@example.com
      id: 3
      tags:
      - mozreview-request
      text:
      - Created attachment 2
      - Bug 1 - Foo 2
      - ''
      - 'Review commit: http://$DOCKER_HOSTNAME:$HGPORT1/r/3/diff/#index_header'
      - 'See other reviews: http://$DOCKER_HOSTNAME:$HGPORT1/r/3/'
    component: TestComponent
    depends_on: []
    platform: All
    product: TestProduct
    resolution: ''
    status: NEW
    summary: bug1

Pushing from a subdirectory works

  $ mkdir subdir
  $ cd subdir && git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 2 commits for review
  
  commit: 4ba654c Bug 1 - Foo 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: f6c6fd8 Bug 1 - Foo 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Pushing from a worktree works

  $ git worktree add -b foo ../worktree
  Preparing subdir/../worktree (identifier worktree)
  HEAD is now at f6c6fd8 Bug 1 - Foo 2
  $ cd ../worktree && git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 2 commits for review
  
  commit: 4ba654c Bug 1 - Foo 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: f6c6fd8 Bug 1 - Foo 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

hg:// URLs work

  $ git config mozreview.remote hg://${DOCKER_HOSTNAME}:${HGPORT}:http/test-repo
  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 2 commits for review
  
  commit: 4ba654c Bug 1 - Foo 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: f6c6fd8 Bug 1 - Foo 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

Old configuration using an actual git remote works gracefully

  $ git config mozreview.remote review
  $ git remote add review hg::http://$DOCKER_HOSTNAME:$HGPORT/test-repo
  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 2 commits for review
  
  commit: 4ba654c Bug 1 - Foo 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: f6c6fd8 Bug 1 - Foo 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

No "mozreview.remote" defaults to "review"

  $ git config --unset mozreview.remote
  $ git mozreview push
  adding changesets
  adding manifests
  adding file changes
  added 0 changesets with 0 changes to 1 files
  
  submitting 2 commits for review
  
  commit: 4ba654c Bug 1 - Foo 1
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  commit: f6c6fd8 Bug 1 - Foo 2
  review: http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

No "mozreview.remote" and no remote tells to run configure

  $ git remote remove review
  $ git mozreview push
  abort: no review repository defined; run `git mozreview configure`
  [1]

Cleanup

  $ mozreview stop
  stopped 9 containers
