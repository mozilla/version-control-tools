  $ hg init mozilla-central
  $ cat >> mozilla-central/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.treeclosure = python:mozhghooks.treeclosure.hook
  > 
  > [extensions]
  > urlintercept = $TESTDIR/testing/url-intercept.py
  > 
  > [urlintercept]
  > path = $TESTTMP/url
  > EOF

  $ hg clone mozilla-central client
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client

Pushing to an open tree should succeed

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/mozilla-central?format=json
  > {"status": "open", "reason": null}
  > EOF

  $ touch foo
  $ hg commit -A -m 'open tree'
  adding foo
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url

Pushing to a closed tree should fail

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/mozilla-central?format=json
  > {"status": "closed", "reason": "splines won't reticulate"}
  > EOF

  $ echo closed > foo
  $ hg commit -m 'this should fail'
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  Tree mozilla-central is CLOSED! (https://treestatus.mozilla.org/mozilla-central?format=json) - splines won't reticulate
  
  
  ************************** ERROR ****************************
  To push despite the closed tree, include "CLOSED TREE" in your push comment
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.treeclosure hook failed
  [255]

Pushing to a closed tree with the magic words is allowed

  $ hg commit --amend -m 'force push on a CLOSED TREE' > /dev/null
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  Tree mozilla-central is CLOSED! (https://treestatus.mozilla.org/mozilla-central?format=json) - splines won't reticulate
  But you included the magic words.  Hope you had permission!

Pushing multiple changesets to a closed tree is accepted if CLOSED TREE
is on the tip commit

  $ echo dummy1 > foo
  $ hg commit -m 'dummy1'
  $ echo dummy2 > foo
  $ hg commit -m 'dummy2'
  $ echo forceit > foo
  $ hg commit -m 'do it on a CLOSED TREE'
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  intercepting url
  Tree mozilla-central is CLOSED! (https://treestatus.mozilla.org/mozilla-central?format=json) - splines won't reticulate
  But you included the magic words.  Hope you had permission!

Pushing to an approval required tree should fail

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/mozilla-central?format=json
  > {"status": "approval required", "reason": "be verrrry careful"}
  > EOF

  $ echo noapproval > foo
  $ hg commit -m 'no approval'
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  
  
  ************************** ERROR ****************************
  Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\S*=...)
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.treeclosure hook failed
  [255]

Adding an approver should allow pushing on an approval only tree

  $ hg commit --amend -m 'Got approval; a=someone' > /dev/null
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url

Approval of the form "a1.2=foo" works

  $ echo otherform > foo
  $ hg commit -m 'Got approval a1.2=someone'
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url

Approval is only needed on tip-most commit

  $ echo dummy1 > foo
  $ hg commit -m 'dummy1'
  $ echo dummy2 > foo
  $ hg commit -m 'dummy2'
  $ echo tip > foo
  $ hg commit -m 'Got approval; a=someone'
  $ hg push
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  intercepting url

  $ cd ..

Hook should not run when stripping

  $ hg init striptest
  $ cd striptest
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ echo foo > foo
  $ hg commit -m commit1
  $ hg -q up -r 0
  $ echo bar > foo
  $ hg commit -m commit2
  created new head

  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > strip =
  > urlintercept = $TESTDIR/testing/url-intercept.py
  > 
  > [urlintercept]
  > path = $TESTTMP/url
  > 
  > [hooks]
  > pretxnchangegroup.treeclosure = python:mozhghooks.treeclosure.hook
  > EOF

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/striptest?format=json
  > {"status": "approval required", "reason": "it does not matter"}
  > EOF

  $ hg strip -r 1 --no-backup

  $ hg log -T '{rev} {desc}\n'
  1 commit2
  0 initial
