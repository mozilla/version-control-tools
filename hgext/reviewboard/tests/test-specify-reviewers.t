#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Enable obsolescence so we can test code paths which use it.

  $ cat >> client/.hg/hgrc << EOF
  > [experimental]
  > evolution = all
  > EOF

Create an initial commit.

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Add some potential reviewers.

  $ mozreview create-user romulus@example.com password 'Romulus :romulus'
  Created user 6
  $ mozreview create-user remus@example.com password 'Remus :remus'
  Created user 7

We create a user with a name which contains another user name as a prefix to
exercise the code path where multiple users are returned for a query.

  $ mozreview create-user remus2@example.com password 'Remus2 :remus2'
  Created user 8

We create a user who has decided to capitalize their ircnick.

  $ mozreview create-user ryanvm@example.com password 'Ryan :RyanVM'
  Created user 9

Try a bunch of different ways of specifying a reviewer

  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg commit -m 'Bug 1 - some stuff; r?romulus'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; r?romulus, r?remus'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; r?romulus,r?remus'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; r?romulus, remus'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; r?romulus,remus'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; (r?romulus)'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; (r?romulus,remus)'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; [r?romulus]'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; [r?remus, r?romulus]'
  $ echo blah >> foo
  $ hg commit -m 'Bug 1 - More stuff; r?romulus, r=test-only'
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 10 changesets)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 11 changesets with 11 changes to 1 files
  remote: recorded push in pushlog
  submitting 10 changesets for review
  unrecognized reviewer: test-only
  
  changeset:  11:7122d7b3a455
  summary:    Bug 1 - some stuff; r?romulus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  12:1cac575c1bc7
  summary:    Bug 1 - More stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  13:39c50951b7d1
  summary:    Bug 1 - More stuff; r?romulus,r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  14:b4ea260242b6
  summary:    Bug 1 - More stuff; r?romulus, remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  changeset:  15:a67020c63164
  summary:    Bug 1 - More stuff; r?romulus,remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6 (draft)
  
  changeset:  16:9c52c338c619
  summary:    Bug 1 - More stuff; (r?romulus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/7 (draft)
  
  changeset:  17:b04b8d95503b
  summary:    Bug 1 - More stuff; (r?romulus,remus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/8 (draft)
  
  changeset:  18:ccfcf9b70a65
  summary:    Bug 1 - More stuff; [r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/9 (draft)
  
  changeset:  19:214fce360842
  summary:    Bug 1 - More stuff; [r?remus, r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/10 (draft)
  
  changeset:  20:1bc0bf6f1f8b
  summary:    Bug 1 - More stuff; r?romulus, r=test-only
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/11 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)

  $ rbmanage list-reviewers 2 --draft
  romulus

  $ rbmanage list-reviewers 3 --draft
  remus, romulus

  $ rbmanage list-reviewers 4 --draft
  remus, romulus

  $ rbmanage list-reviewers 5 --draft
  remus, romulus

  $ rbmanage list-reviewers 6 --draft
  remus, romulus

  $ rbmanage list-reviewers 7 --draft
  romulus

  $ rbmanage list-reviewers 8 --draft
  remus, romulus

  $ rbmanage list-reviewers 9 --draft
  romulus

  $ rbmanage list-reviewers 10 --draft
  remus, romulus

  $ rbmanage list-reviewers 11 --draft
  romulus

The review state file should have reviewers recorded

  $ cat .hg/reviewboard/review/10.state
  public False
  reviewers remus,romulus
  status pending

Publishing series during push works

  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  no changes found
  submitting 10 changesets for review
  
  changeset:  11:7122d7b3a455
  summary:    Bug 1 - some stuff; r?romulus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  12:1cac575c1bc7
  summary:    Bug 1 - More stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  13:39c50951b7d1
  summary:    Bug 1 - More stuff; r?romulus,r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  14:b4ea260242b6
  summary:    Bug 1 - More stuff; r?romulus, remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  changeset:  15:a67020c63164
  summary:    Bug 1 - More stuff; r?romulus,remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6 (draft)
  
  changeset:  16:9c52c338c619
  summary:    Bug 1 - More stuff; (r?romulus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/7 (draft)
  
  changeset:  17:b04b8d95503b
  summary:    Bug 1 - More stuff; (r?romulus,remus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/8 (draft)
  
  changeset:  18:ccfcf9b70a65
  summary:    Bug 1 - More stuff; [r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/9 (draft)
  
  changeset:  19:214fce360842
  summary:    Bug 1 - More stuff; [r?remus, r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/10 (draft)
  
  changeset:  20:1bc0bf6f1f8b
  summary:    Bug 1 - More stuff; r?romulus, r=test-only
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/11 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)
  [1]

  $ rbmanage dumpreview 10
  id: 10
  status: pending
  public: true
  bugs:
  - '1'
  commit: null
  submitter: default+5
  summary: Bug 1 - More stuff; [r?remus, r?romulus]
  description:
  - Bug 1 - More stuff; [r?remus, r?romulus]
  - ''
  - 'MozReview-Commit-ID: cXO9WC'
  target_people:
  - remus
  - romulus
  extra_data:
    calculated_trophies: true
  commit_extra_data:
    p2rb: true
    p2rb.author: test
    p2rb.commit_id: 214fce3608426755a50ae60ae8645eb9bc1f7537
    p2rb.commit_message_filediff_ids: '{"1": 18}'
    p2rb.commit_message_filename: commit-message-ccfcf
    p2rb.first_public_ancestor: 3a9f6899ef84c99841f546030b036d0124a863cf
    p2rb.identifier: bz://1/mynick
    p2rb.is_squashed: false
  diffs:
  - id: 11
    revision: 1
    base_commit_id: ccfcf9b70a65731d01240f24815edf0cf6b64739
    name: diff
    extra: {}
    patch:
    - diff --git a/foo b/foo
    - '--- a/foo'
    - +++ b/foo
    - '@@ -1,8 +1,9 @@'
    - ' initial'
    - ' blah'
    - ' blah'
    - ' blah'
    - ' blah'
    - ' blah'
    - ' blah'
    - ' blah'
    - +blah
    - ''
  approved: false
  approval_failure: A suitable reviewer has not given a "Ship It!"

Amending a commit should also work. This exercises the update_review_request
code path.

  $ echo blah >> foo
  $ hg commit --amend -l - << EOF
  > Bug 1 - Even more stuff; r?romulus, r?remus
  > 
  > MozReview-Commit-ID: hE3OiG
  > EOF
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 10 changesets for review
  
  changeset:  11:7122d7b3a455
  summary:    Bug 1 - some stuff; r?romulus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  12:1cac575c1bc7
  summary:    Bug 1 - More stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  13:39c50951b7d1
  summary:    Bug 1 - More stuff; r?romulus,r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4
  
  changeset:  14:b4ea260242b6
  summary:    Bug 1 - More stuff; r?romulus, remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5
  
  changeset:  15:a67020c63164
  summary:    Bug 1 - More stuff; r?romulus,remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6
  
  changeset:  16:9c52c338c619
  summary:    Bug 1 - More stuff; (r?romulus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/7
  
  changeset:  17:b04b8d95503b
  summary:    Bug 1 - More stuff; (r?romulus,remus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/8
  
  changeset:  18:ccfcf9b70a65
  summary:    Bug 1 - More stuff; [r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/9
  
  changeset:  19:214fce360842
  summary:    Bug 1 - More stuff; [r?remus, r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/10
  
  changeset:  22:47ac4d7af91f
  summary:    Bug 1 - Even more stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/11 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)
 
  $ rbmanage list-reviewers 11
  remus, romulus

We should not overwrite manually added reviewers when the revision is pushed
again.

  $ rbmanage add-reviewer 11 --user admin+1
  3 people listed on review request
  $ rbmanage list-reviewers 11 --draft
  admin+1, remus, romulus
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  no changes found
  submitting 10 changesets for review
  
  changeset:  11:7122d7b3a455
  summary:    Bug 1 - some stuff; r?romulus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  12:1cac575c1bc7
  summary:    Bug 1 - More stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  13:39c50951b7d1
  summary:    Bug 1 - More stuff; r?romulus,r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4
  
  changeset:  14:b4ea260242b6
  summary:    Bug 1 - More stuff; r?romulus, remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5
  
  changeset:  15:a67020c63164
  summary:    Bug 1 - More stuff; r?romulus,remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6
  
  changeset:  16:9c52c338c619
  summary:    Bug 1 - More stuff; (r?romulus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/7
  
  changeset:  17:b04b8d95503b
  summary:    Bug 1 - More stuff; (r?romulus,remus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/8
  
  changeset:  18:ccfcf9b70a65
  summary:    Bug 1 - More stuff; [r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/9
  
  changeset:  19:214fce360842
  summary:    Bug 1 - More stuff; [r?remus, r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/10
  
  changeset:  22:47ac4d7af91f
  summary:    Bug 1 - Even more stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/11 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)
  [1]
  $ rbmanage list-reviewers 11
  admin+1, remus, romulus

We should not overwrite manually added reviewers if the revision is amended
and pushed with no reviewers specified.

  $ rbmanage list-reviewers 11
  admin+1, remus, romulus
  $ echo blah >> foo
  $ hg commit --amend -l - << EOF
  > Bug 1 - Amended stuff
  > 
  > MozReview-Commit-ID: hE3OiG
  > EOF
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 10 changesets for review
  
  changeset:  11:7122d7b3a455
  summary:    Bug 1 - some stuff; r?romulus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  12:1cac575c1bc7
  summary:    Bug 1 - More stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  13:39c50951b7d1
  summary:    Bug 1 - More stuff; r?romulus,r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4
  
  changeset:  14:b4ea260242b6
  summary:    Bug 1 - More stuff; r?romulus, remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5
  
  changeset:  15:a67020c63164
  summary:    Bug 1 - More stuff; r?romulus,remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6
  
  changeset:  16:9c52c338c619
  summary:    Bug 1 - More stuff; (r?romulus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/7
  
  changeset:  17:b04b8d95503b
  summary:    Bug 1 - More stuff; (r?romulus,remus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/8
  
  changeset:  18:ccfcf9b70a65
  summary:    Bug 1 - More stuff; [r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/9
  
  changeset:  19:214fce360842
  summary:    Bug 1 - More stuff; [r?remus, r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/10
  
  changeset:  24:cf273a4d0f27
  summary:    Bug 1 - Amended stuff
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/11 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

  $ rbmanage list-reviewers 11
  admin+1, remus, romulus

Amending a commit with reviewers specified will reset the reviewers back to
those specified in the commit summary.

  $ echo blah >> foo
  $ hg commit --amend -l - << EOF
  > Bug 1 - Amended stuff; r?romulus, r?remus
  > 
  > MozReview-Commit-ID: vI38IS
  > EOF
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  submitting 10 changesets for review
  
  changeset:  11:7122d7b3a455
  summary:    Bug 1 - some stuff; r?romulus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2
  
  changeset:  12:1cac575c1bc7
  summary:    Bug 1 - More stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3
  
  changeset:  13:39c50951b7d1
  summary:    Bug 1 - More stuff; r?romulus,r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4
  
  changeset:  14:b4ea260242b6
  summary:    Bug 1 - More stuff; r?romulus, remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5
  
  changeset:  15:a67020c63164
  summary:    Bug 1 - More stuff; r?romulus,remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6
  
  changeset:  16:9c52c338c619
  summary:    Bug 1 - More stuff; (r?romulus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/7
  
  changeset:  17:b04b8d95503b
  summary:    Bug 1 - More stuff; (r?romulus,remus)
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/8
  
  changeset:  18:ccfcf9b70a65
  summary:    Bug 1 - More stuff; [r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/9
  
  changeset:  19:214fce360842
  summary:    Bug 1 - More stuff; [r?remus, r?romulus]
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/10
  
  changeset:  26:7a590575b558
  summary:    Bug 1 - Amended stuff; r?romulus, r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/11 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 1)

  $ rbmanage list-reviewers 11
  remus, romulus

Unrecognized reviewers should be ignored

  $ hg phase --public -r .
  $ bugzilla create-bug TestProduct TestComponent 'Second Bug'
  $ echo blah >> foo
  $ hg commit -m 'Bug 2 - different stuff; r?cthulhu'
  $ hg push --reviewid 2
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  unrecognized reviewer: cthulhu
  
  changeset:  28:c0f7a0ead8a3
  summary:    Bug 2 - different stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/13 (draft)
  
  review id:  bz://2/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/12 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 12)
  $ rbmanage list-reviewers 12
  

Reviewer identification should be case insensitive.

  $ echo blah >> foo
  $ hg commit -m 'Bug 2 - better stuff; r?ryanvm'
  $ hg push -c .
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  30:d78ae37a43e4
  summary:    Bug 2 - better stuff; r?ryanvm
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/14 (draft)
  
  review id:  bz://2/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/12 (draft)
  
  publish these review requests now (Yn)?  y
  (published review request 12)

  $ rbmanage list-reviewers 14
  RyanVM

Reviewer deduction can be disabled with a config option.

  $ echo blah >> foo
  $ hg commit -m 'Bug 2 - awesome stuff; r?remus'
  $ hg push -c . --config reviewboard.deduce-reviewers=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  32:8156d1d4e67f
  summary:    Bug 2 - awesome stuff; r?remus
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/15 (draft)
  
  review id:  bz://2/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/12 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  
  publish these review requests now (Yn)?  y
  (published review request 12)

  $ rbmanage list-reviewers 15
  

Cleanup

  $ mozreview stop
  stopped 9 containers
