#require docker

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
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 1 changesets for review
  
  changeset:  1:7194ef3a2eac
  summary:    Bug 1 - some stuff
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)

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
  (200, u'{\n  "destination": "try", \n  "error_msg": "hg error in cmd: hg pull test-repo -r 42: pulling from http://hgrb/test-repo\\nabort: unknown revision \'42\'!\\n", \n  "landed": false, \n  "push_bookmark": "", \n  "result": "", \n  "rev": "42", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')

Post a job

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898
  (200, u'{\n  "request_id": 2\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 2 --poll
  (200, u'{\n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "", \n  "result": "*", \n  "rev": "7194ef3a2eac", \n  "tree": "test-repo", \n  "trysyntax": ""\n}') (glob)

Post a job with try syntax

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898 --trysyntax "stuff"
  (200, u'{\n  "request_id": 3\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 3 --poll
  (200, u'{\n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "", \n  "result": "*", \n  "rev": "7194ef3a2eac", \n  "tree": "test-repo", \n  "trysyntax": "stuff"\n}') (glob)

Post a job using a bookmark

  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - some stuff'
  $ hg push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  submitting 2 changesets for review
  
  changeset:  1:7194ef3a2eac
  summary:    Bug 1 - some stuff
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  changeset:  2:53b624fb3597
  summary:    Bug 1 - some stuff
  review:     http://*:$HGPORT1/r/3 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898 --push-bookmark "bookmark"
  (200, u'{\n  "request_id": 4\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 4 --poll
  (200, u'{\n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "push_bookmark": "bookmark", \n  "result": "*", \n  "rev": "53b624fb3597", \n  "tree": "test-repo", \n  "trysyntax": ""\n}') (glob)

Getting status for an unknown job should return a 404

  $ ottoland autoland-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

Posting a pullrequest job with bad credentials should fail

  $ ottoland post-pullrequest-job $AUTOLAND_URL user repo 1 mozreview 1 cookie http://localhost:9898 --bugid 1 --user blah --password blah
  (401, u'Login required')

Post a pullrequest job. We should generate a login cookie here, but this
functionality is broken (see Bug 1159271). We plan to change over to Bugzilla
tokens prior to deploying this anyway, so there is not much point in fixing
things here.

  $ ottoland post-pullrequest-job $AUTOLAND_URL user repo 1 test-repo 1 cookie http://localhost:9898 --bugid 1
  (200, u'{\n  "request_id": 5\n}')
  $ ottoland pullrequest-job-status $AUTOLAND_URL 5
  (200, u'{\n  "bugid": 1, \n  "destination": "test-repo", \n  "error_msg": null, \n  "landed": null, \n  "pullrequest": 1, \n  "repo": "repo", \n  "result": "", \n  "user": "user"\n}')

Posting a pullrequest job without a bugid should automatically file a bug for the user.
TODO: We should verify that the bug is created once we are using tokens and this
command can succeed.

  $ ottoland post-pullrequest-job $AUTOLAND_URL user repo 1 test-repo 1 cookie http://localhost:9898
  (200, u'{\n  "request_id": 6\n}')
  $ ottoland pullrequest-job-status $AUTOLAND_URL 6
  (200, u'{\n  "bugid": null, \n  "destination": "test-repo", \n  "error_msg": null, \n  "landed": null, \n  "pullrequest": 1, \n  "repo": "repo", \n  "result": "", \n  "user": "user"\n}')

Getting status for an unknown job should return a 404

  $ ottoland pullrequest-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

  $ mozreview stop
  stopped 8 containers
