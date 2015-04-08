#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Posting a job with bad credentials should fail

  $ ottoland post-autoland-job $AUTOLAND_URL mozilla-central 1 try http://localhost:9898 --user blah --password blah
  (401, u'Login required')

Post a job

  $ ottoland post-autoland-job $AUTOLAND_URL mozilla-central 1 try http://localhost:9898
  (200, u'{\n  "request_id": 1\n}')

Get job status

  $ ottoland autoland-job-status $AUTOLAND_URL 1
  (200, u'{\n  "destination": "try", \n  "error_msg": null, \n  "landed": null, \n  "result": "", \n  "rev": "1", \n  "tree": "mozilla-central", \n  "trysyntax": ""\n}')

Getting status for an unknown job should return a 404

  $ ottoland autoland-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

Posting a pullrequest job with bad credentials should fail

  $ ottoland post-pullrequest-job $AUTOLAND_URL user repo 1 mozreview 1 cookie 1 http://localhost:9898 --user blah --password blah
  (401, u'Login required')

Post a pullrequest job

  $ ottoland post-pullrequest-job $AUTOLAND_URL user repo 1 mozreview 1 cookie 1 http://localhost:9898
  (200, u'{\n  "request_id": 1\n}')

Get pullrequest job status

  $ ottoland pullrequest-job-status $AUTOLAND_URL 1
  (200, u'{\n  "bugid": 1, \n  "destination": "mozreview", \n  "error_msg": null, \n  "landed": null, \n  "pullrequest": 1, \n  "repo": "repo", \n  "result": "", \n  "user": "user"\n}')

Getting status for an unknown job should return a 404

  $ ottoland pullrequest-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

  $ mozreview stop
  stopped 8 containers
