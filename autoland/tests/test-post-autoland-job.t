#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Posting a job with bad credentials should fail

  $ ottoland post-autoland-job $AUTOLAND_URL try 1 mozilla-inbound http://localhost --user blah --password blah
  (401, u'Login required')

Post a job

  $ ottoland post-autoland-job $AUTOLAND_URL try 1 mozilla-inbound http://localhost
  (200, u'{\n  "request_id": 1\n}')

Get job status

  $ ottoland autoland-job-status $AUTOLAND_URL 1
  (200, u'{\n  "destination": "mozilla-inbound", \n  "error_msg": null, \n  "landed": null, \n  "pingback_url": "http://localhost", \n  "rev": "1", \n  "tree": "try", \n  "trysyntax": ""\n}')

Getting status for an unknown job should return a 404

  $ ottoland autoland-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

  $ mozreview stop
  stopped 5 containers
