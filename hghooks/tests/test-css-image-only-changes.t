  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.verify-css-image-only-approvals = python:mozhghooks.verify-css-image-only-approvals.hook
  > pretxnchangegroup.treeclosure = python:mozhghooks.treeclosure.hook
  > 
  > [extensions]
  > urlintercept = $TESTDIR/testing/url-intercept.py
  > 
  > [urlintercept]
  > path = $TESTTMP/url
  > EOF

Mark the tree here as approval-required

  $ cat > $TESTTMP/url << EOF
  > https://api.pub.build.mozilla.org/treestatus/trees/server
  > {"result": {"status": "approval required", "reason": "be verrrry careful"}}
  > EOF


Add file (tracked extension), no approval flag, should not work because approval is required

  $ hg init client
  $ cd client
  $ echo "Some SVG" >> test.svg
  $ hg commit -A -m "Change SVG without any approval"
  adding test.svg
  $ hg push ../server
  pushing to ../server
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



Add file (untracked extension), no approval flag, should not work because approval is required

  $ echo "Something else" >> test.txt
  $ hg commit -A -m "Change other file without any approval"
  adding test.txt
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  intercepting url
  
  
  ************************** ERROR ****************************
  Pushing to an APPROVAL REQUIRED tree requires your top changeset comment to include: a=... (or, more accurately, a\S*=...)
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.treeclosure hook failed
  [255]



Tidy up the previous commits
Hook shouldn't run when stripping:
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > strip =
  > 
  > EOF
  $ hg strip -r 0:1 --no-backup
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg parent --template '{rev}\n'


Add file (tracked extension), approval flag, should work

  $ echo "Some more SVG" >> test.svg
  $ hg commit -A -m "Change SVG with a=css-image-only"
  adding test.svg
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  Thanks for your a=css-image-only push, it's the best!
  intercepting url

Add file (untracked extension), approval flag, should fail

  $ echo "Some other things" >> test.txt
  $ hg commit -A -m "Change non-SVG with a=css-image-only"
  adding test.txt
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  ************************** ERROR ****************************
  * non-image/css-file (test.txt) altered in this changeset
  
  You used the a=css-image-only approval message, but your change
  included non-CSS/image/jar.mn changes. Please get "normal"
  approval from release management for your changes.
  *************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.verify-css-image-only-approvals hook failed
  [255]

Add file (untracked extension), generic approval flag, should work
  $ echo "Some other things" >> test.txt
  $ hg commit -A -m "Change non-SVG with a=actual-approval"
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  intercepting url

