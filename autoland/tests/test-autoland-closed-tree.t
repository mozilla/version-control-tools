#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Create a 'try' tree in treestatus

  $ treestatus add-tree ${TREESTATUS_URL} try

Create an initial revision.

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Create a commit to test on Try

  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg commit -m 'Bug 1 - some stuff'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/99de87c26bf8-5c89fdb9-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:7194ef3a2eac
  summary:    Bug 1 - some stuff
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

Close the tree

  $ treestatus set-status $TREESTATUS_URL try closed

Post a job

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898
  (200, u'{\n  "request_id": 1\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 1 --poll
  timed out

Open the tree

  $ treestatus set-status $TREESTATUS_URL try open
  $ ottoland autoland-job-status $AUTOLAND_URL 1 --poll
  (200, u'{\n  "commit_descriptions": "", \n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "", \n  "result": "7194ef3a2eac", \n  "rev": "7194ef3a2eac", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')

  $ mozreview stop
  stopped 10 containers
