#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv
  $ mozreview create-user cthulhu@example.com password 'Cthulhu :cthulhu'
  Created user 6

Create an initial revision.

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Create a commit to test on Try

  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg commit -m 'Bug 1 - some stuff; r?cthulhu'
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/633b0929fc18-25aef645-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:e2507be7827c
  summary:    Bug 1 - some stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)
  $ REV=`hg log -r . --template "{node|short}"`
  $ REV_NO=`hg log -r . --template "{rev}"`

Ensure Autoland started without errors

  $ mozreview exec autoland tail -n 20 /home/autoland/autoland.log
  starting autoland
  * autoland INFO starting autoland (glob)

Posting a job with bad credentials should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p$REV_NO try http://localhost:9898 --user blah --password blah --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (401, u'Login required')
  $ mozreview exec autoland tail -n1 /var/log/apache2/error.log
  * WARNING:root:Failed authentication for "blah" from * (glob)

Post a job from s3 url

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p0 inbound http://localhost:9898 --patch-url "s3://example-bucket/p1.patch"
  (200, u'{\n  "request_id": 1\n}')

Post a job from localhost

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p1 inbound http://localhost:9898 --patch-url "http://localhost/path/to/p0.patch"
  (200, u'{\n  "request_id": 2\n}')

Post a job from http url

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p2 inbound http://localhost:9898 --patch-url "http://example.com/p2.patch"
  (400, u'{\n  "error": "Bad request: bad patch_url"\n}')

Post a job with try syntax

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p3 try http://localhost:9898 --trysyntax "stuff" --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (400, u'{\n  "error": "Bad request: trysyntax is not supported with patch_urls"\n}')

Post a job using a bookmark

  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - more goodness; r?cthulhu'
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 2 changesets for review
  
  changeset:  1:e2507be7827c
  summary:    Bug 1 - some stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:373b6ff60965
  summary:    Bug 1 - more goodness; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)
  $ REV=`hg log -r . --template "{node|short}"`

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p4 inbound http://localhost:9898 --push-bookmark "bookmark" --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 3\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 3 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "patch based landings not implemented", \n  "landed": false, \n  "ldap_username": "autolanduser@example.com", \n  "patch_urls": [\n    "http://$DOCKER_HOSTNAME:$HGPORT/test-repo/raw-rev/373b6ff60965"\n  ], \n  "push_bookmark": "bookmark", \n  "result": "", \n  "rev": "p4", \n  "tree": "test-repo"\n}')
  $ mozreview exec autoland hg log /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'

Getting status for an unknown job should return a 404

  $ ottoland autoland-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

  $ mozreview exec autoland hg log --encoding=utf-8 /repos/test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'

  $ mozreview exec autoland hg log /repos/try/ --template '{rev}:{desc\|firstline}:{phase}\\n'

  $ mozreview exec autoland hg log --encoding=utf-8 /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'

Test pingback url whitelist.  localhost, private IPs, and example.com are in
the whitelist. example.org is not.

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p5 inbound1 http://example.com:9898 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 4\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p6 inbound2 http://localhost --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 5\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p7 inbound3 http://127.0.0.1 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 6\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p8 inbound4 http://192.168.0.1 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 7\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p9 inbound5 http://172.16.0.1 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 8\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p10 inbound6 http://10.0.0.1:443 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 9\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p11 inbound7 http://8.8.8.8:443 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (400, u'{\n  "error": "Bad request: bad pingback_url"\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p12 inbound8 http://example.org:9898 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (400, u'{\n  "error": "Bad request: bad pingback_url"\n}')

Post the same job twice.  Start with stopping the autoland service to
guarentee the first request is still in the queue when the second is submitted.

  $ PID=`mozreview exec autoland ps x | grep autoland.py | grep -v grep | awk '{ print $1 }'`
  $ mozreview exec autoland kill $PID
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo $REV try http://localhost:9898 --trysyntax "stuff"
  (200, u'{\n  "request_id": 10\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo $REV try http://localhost:9898 --trysyntax "stuff"
  (400, u'{\n  "error": "Bad Request: a request to land revision 373b6ff60965 to try is already in progress"\n}')

  $ mozreview stop
  stopped 9 containers
