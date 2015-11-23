#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

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

Ensure Autoland started without errors

  $ mozreview exec autoland tail -n 20 /home/ubuntu/autoland.log
   0:00.* LOG: MainThread INFO starting autoland (glob)

Posting a job with bad credentials should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898 --user blah --password blah
  (401, u'Login required')

Posting a job with an unknown revision should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo 42 try http://localhost:9898
  (200, u'{\n  "request_id": 1\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 1 --poll
  (200, u'{\n  "commit_descriptions": "", \n  "destination": "try", \n  "error_msg": "hg error in cmd: hg pull test-repo -r 42: pulling from http://hgrb/test-repo\\nabort: unknown revision \'42\'!\\n", \n  "landed": false, \n  "push_bookmark": "", \n  "result": "", \n  "rev": "42", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')

Post a job

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898
  (200, u'{\n  "request_id": 2\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 2 --poll
  (200, u'{\n  "commit_descriptions": "", \n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "", \n  "result": "*", \n  "rev": "7194ef3a2eac", \n  "tree": "test-repo", \n  "trysyntax": ""\n}') (glob)

Post a job with try syntax

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898 --trysyntax "stuff"
  (200, u'{\n  "request_id": 3\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 3 --poll
  (200, u'{\n  "commit_descriptions": "", \n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "", \n  "result": "*", \n  "rev": "7194ef3a2eac", \n  "tree": "test-repo", \n  "trysyntax": "stuff"\n}') (glob)

Post a job using a bookmark

  $ echo foo2 > foo
  $ hg commit --encoding utf-8 -m 'Bug 1 - こんにちは'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:7194ef3a2eac
  summary:    Bug 1 - some stuff
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:7561731d264a
  summary:    Bug 1 - ?????
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898 --push-bookmark "bookmark"
  (200, u'{\n  "request_id": 4\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 4 --poll
  (200, u'{\n  "commit_descriptions": "", \n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "bookmark", \n  "result": "7561731d264a", \n  "rev": "7561731d264a", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')

Post a job with commit descriptions to be rewritten

  $ REV=`hg log -r . --template "{node|short}"`
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo $REV try http://localhost:9898 --commit-descriptions "{\"$REV\": \"even better \\u3053\\u3093\\u306b\\u3061\\u306f\"}"
  (200, u'{\n  "request_id": 5\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 5 --poll
  (200, u'{\n  "commit_descriptions": {\n    "7561731d264a": "even better \\u3053\\u3093\\u306b\\u3061\\u306f"\n  }, \n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "", \n  "result": "7561731d264a", \n  "rev": "7561731d264a", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')

Getting status for an unknown job should return a 404

  $ ottoland autoland-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

  $ mozreview stop
  stopped 10 containers
