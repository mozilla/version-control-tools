  $ hg init comm-central
  $ cat >> comm-central/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.treeclosure_comm_central = python:mozhghooks.treeclosure_comm_central.hook
  > 
  > [extensions]
  > urlintercept = $TESTDIR/testing/url-intercept.py
  > 
  > [urlintercept]
  > path = $TESTTMP/url
  > EOF

  $ hg clone comm-central client
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mq=
  > EOF

Pushing to an open Thunderbird tree should succeed

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-thunderbird?format=json
  > {"status": "open", "reason": ""}
  > EOF

  $ echo thunderbird > testfile
  $ hg commit -A -m 'initial'
  adding testfile
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url

Pushing to an open SeaMonkey tree should succeed
Note that paths under suite/ are treated as seamonkey

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-seamonkey?format=json
  > {"status": "open", "reason": ""}
  > EOF

  $ mkdir -p suite/build
  $ touch suite/build/test
  $ hg commit -A -m 'add suite file'
  adding suite/build/test
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url

Pushing to an open calendar tree should succeed
Note that paths under calendar/ query thunderbird

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-thunderbird?format=json
  > {"status": "open", "reason": ""}
  > EOF

  $ mkdir -p calendar/app
  $ touch calendar/app/test
  $ hg commit -A -m 'add calendar file'
  adding calendar/app/test
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url

Pushing to a closed Thunderbird tree should fail

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-thunderbird?format=json
  > {"status": "closed", "reason": "splines won't reticulate"}
  > EOF

  $ echo closed > testfile
  $ hg commit -m 'Thunderbird is closed'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  Tree Thunderbird comm-central is CLOSED!
  Thunderbird is closed
  
  
  ************************** ERROR ****************************
  To push despite the closed tree, include "CLOSED TREE" in your push comment
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.treeclosure_comm_central hook failed
  [255]

  $ hg strip -r . > /dev/null

Test pushing when SeaMonkey is closed

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-seamonkey?format=json
  > {"status": "closed", "reason": "splines won't reticulate"}
  > EOF

  $ echo closed > suite/build/test
  $ hg commit -m 'Test SeaMonkey push'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  Tree Seamonkey comm-central is CLOSED!
  Test SeaMonkey push
  
  
  ************************** ERROR ****************************
  To push despite the closed tree, include "CLOSED TREE" in your push comment
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.treeclosure_comm_central hook failed
  [255]

  $ hg strip -r . > /dev/null

Test pushing when calendar is closed

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-thunderbird?format=json
  > {"status": "closed", "reason": "splines won't reticulate"}
  > EOF

  $ echo calendarclosed > calendar/app/test
  $ hg commit -m 'Calendar is closed'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  Tree Thunderbird comm-central is CLOSED!
  Calendar is closed
  
  
  ************************** ERROR ****************************
  To push despite the closed tree, include "CLOSED TREE" in your push comment
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.treeclosure_comm_central hook failed
  [255]

Adding CLOSED TREE allows the push to go through

  $ hg commit --amend -m 'Forcing it on a CLOSED TREE' > /dev/null
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  Tree Thunderbird comm-central is CLOSED!
  Forcing it on a CLOSED TREE
  But you included the magic words.  Hope you had permission!

And the same for SeaMonkey

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-seamonkey?format=json
  > {"status": "closed", "reason": "splines won't reticulate"}
  > EOF

  $ echo forcing > suite/build/test
  $ hg commit -m 'Forcing SeaMonkey on a CLOSED TREE'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url
  Tree Seamonkey comm-central is CLOSED!
  Forcing SeaMonkey on a CLOSED TREE
  But you included the magic words.  Hope you had permission!

CLOSED TREE only needed on tip commit

  $ echo dummy1 > suite/build/test
  $ hg commit -m 'dummy1'
  $ echo dummy2 > suite/build/test
  $ hg commit -m 'dummy2'
  $ echo real > suite/build/test
  $ hg commit -m 'Multiple commits on a CLOSED TREE'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  intercepting url
  Tree Seamonkey comm-central is CLOSED!
  Multiple commits on a CLOSED TREE
  But you included the magic words.  Hope you had permission!

Approval required is enforced

  $ cat > $TESTTMP/url << EOF
  > https://treestatus.mozilla.org/comm-central-thunderbird?format=json
  > {"status": "approval required", "reason": ""}
  > EOF

  $ echo approval > testfile
  $ hg commit -m 'checkin 1'
  $ hg push
  pushing to $TESTTMP/comm-central
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
  abort: pretxnchangegroup.treeclosure_comm_central hook failed
  [255]

Use the magic words to bypass approval

  $ echo gotit > testfile
  $ hg commit -m 'Got approval; a=foo'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  intercepting url

Also check a1.2=foo approval syntax works

  $ echo syntax > testfile
  $ hg commit -m 'Got approval a1.2=someone'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  intercepting url

Approval on multiple changesets only requires tip

  $ echo dummy1 > testfile
  $ hg commit -m 'dummy1'
  $ echo dummy2 > testfile
  $ hg commit -m 'dummy2'
  $ echo approval > testfile
  $ hg commit -m 'final checkin a=someone'
  $ hg push
  pushing to $TESTTMP/comm-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  intercepting url
