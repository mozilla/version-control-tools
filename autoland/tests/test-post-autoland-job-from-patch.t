#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv
  $ mozreview create-user cthulhu@example.com password 'Cthulhu :cthulhu'
  Created user 6
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ cd client

Create a commit to test

  $ echo initial > foo
  $ hg commit -A -m 'Bug 1 - some stuff; r?cthulhu'
  adding foo
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  0:4b444b4e2552
  summary:    Bug 1 - some stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)
  $ REV=`hg log -r . --template "{node|short}"`

Ensure Autoland started without errors

  $ mozreview exec autoland tail -n 20 /home/autoland/autoland.log
  starting autoland
  * autoland INFO starting autoland (glob)

Posting a job with bad credentials should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p0 try http://localhost:9898 --user blah --password blah --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (401, u'Login required')
  $ mozreview exec autoland tail -n1 /var/log/apache2/error.log
  * WARNING:root:Failed authentication for "blah" from * (glob)
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p0 try http://localhost:9898 --user blah --password '' --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (401, u'Login required')
  $ mozreview exec autoland tail -n1 /var/log/apache2/error.log
  * WARNING:root:Failed authentication for "blah" from * (glob)

Post a job from http url should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p1 inbound http://localhost:9898 --patch-url http://example.com/p2.patch
  (400, u'{\n  "error": "Bad request: bad patch_url"\n}')

Post a job from s3 url.  This should fail because we don't have a mock
environment for S3.

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p2 inbound http://localhost:9898 --patch-url s3://example-bucket/p1.patch
  (200, u'{\n  "request_id": 1\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 1 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "unable to download s3://example-bucket/p1.patch: permission denied", \n  "landed": false, \n  "ldap_username": "autolanduser@example.com", \n  "patch_urls": [\n    "s3://example-bucket/p1.patch"\n  ], \n  "result": "", \n  "rev": "p2", \n  "tree": "test-repo"\n}')

Post a job from private ip

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p3 inbound http://localhost:9898 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 2\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 2 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "patch_urls": [\n    "http://$DOCKER_HOSTNAME:$HGPORT/test-repo/raw-rev/4b444b4e2552"\n  ], \n  "result": "4b444b4e255243491f85995636b268ce9d3289e5", \n  "rev": "p3", \n  "tree": "test-repo"\n}')
  $ mozreview exec autoland hg log /repos/test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  0:Bug 1 - some stuff; r?cthulhu:public

Post a job using an inline patch

  $ echo foo2 > foo
  $ hg commit -m 'Bug 1 - some more stuff; r?cthulhu'
  $ hg export > $TESTTMP/patch
  $ hg push --config reviewboard.autopublish=false -c .
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/18c39f487c3e*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:51664e0c33c2
  summary:    Bug 1 - some more stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p4 inbound http://localhost:9898 --push-bookmark "bookmark" --patch-file $TESTTMP/patch
  (200, u'{\n  "request_id": 3\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 3 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "patch": "*", \n  "push_bookmark": "bookmark", \n  "result": "18c39f487c3e92d6e6f51a7690def09afb35bd73", \n  "rev": "p4", \n  "tree": "test-repo"\n}') (glob)
  $ mozreview exec autoland hg log /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  1:Bug 1 - some more stuff; r?cthulhu:public
  0:Bug 1 - some stuff; r?cthulhu:public

Post a job using an inline patch with 'Diff Start Line'

  $ echo foo3 > foo
  $ hg commit -m 'Bug 1 - even more stuff; r?cthulhu'
  $ hg export > $TESTTMP/patch2
  $ DSL=`cat -n $TESTTMP/patch2 | grep 'diff ' | head -n 1 | awk '{print $1+1}'`
  $ perl -pe 's/^(# User)/# Diff Start Line '$DSL'\n$1/' < $TESTTMP/patch2 > $TESTTMP/patch
  $ hg push --config reviewboard.autopublish=false -c .
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/60bcf02d3611*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  2:3c9a0891b189
  summary:    Bug 1 - even more stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p4 inbound http://localhost:9898 --push-bookmark "bookmark" --patch-file $TESTTMP/patch
  (200, u'{\n  "request_id": 4\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 4 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "patch": "*", \n  "push_bookmark": "bookmark", \n  "result": "6eeb07132e29cf03fb10316b603e6a7596711736", \n  "rev": "p4", \n  "tree": "test-repo"\n}') (glob)
  $ mozreview exec autoland hg log /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  2:Bug 1 - even more stuff; r?cthulhu:public
  1:Bug 1 - some more stuff; r?cthulhu:public
  0:Bug 1 - some stuff; r?cthulhu:public

Post a job using a bookmark

  $ echo foo4 > foo
  $ hg commit -m 'Bug 1 - more goodness; r?cthulhu'
  $ hg push --config reviewboard.autopublish=false -c .
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/415a7c414baa*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  3:a5988e16f939
  summary:    Bug 1 - more goodness; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)
  $ REV=`hg log -r . --template "{node|short}"`

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p5 inbound http://localhost:9898 --push-bookmark "bookmark" --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 5\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 5 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "patch_urls": [\n    "http://$DOCKER_HOSTNAME:$HGPORT/test-repo/raw-rev/a5988e16f939"\n  ], \n  "push_bookmark": "bookmark", \n  "result": "f236984973792f3af0ed69bb3441f3d41b4135a7", \n  "rev": "p5", \n  "tree": "test-repo"\n}')
  $ mozreview exec autoland hg log /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  3:Bug 1 - more goodness; r?cthulhu:public
  2:Bug 1 - even more stuff; r?cthulhu:public
  1:Bug 1 - some more stuff; r?cthulhu:public
  0:Bug 1 - some stuff; r?cthulhu:public

Post a job with unicode

  $ echo foo5 > foo
  $ hg commit --encoding utf-8 -m 'Bug 1 - こんにちは; r?cthulhu'
  $ hg push --config reviewboard.autopublish=false -c .
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/162f89a57ee8*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  4:c0f22d03c452
  summary:    Bug 1 - ?????; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)
  $ REV=`hg log -r . --template "{node|short}"`
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p6 inbound http://localhost:9898 --push-bookmark "bookmark" --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 6\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 6 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "patch_urls": [\n    "http://$DOCKER_HOSTNAME:$HGPORT/test-repo/raw-rev/c0f22d03c452"\n  ], \n  "push_bookmark": "bookmark", \n  "result": "43859e8d30ccdaf3a7c2461b5fea67da31ce88dd", \n  "rev": "p6", \n  "tree": "test-repo"\n}')
  $ mozreview exec autoland hg log --encoding=utf-8 /repos/test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  4:Bug 1 - \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf; r?cthulhu:public (esc)
  3:Bug 1 - more goodness; r?cthulhu:public
  2:Bug 1 - even more stuff; r?cthulhu:public
  1:Bug 1 - some more stuff; r?cthulhu:public
  0:Bug 1 - some stuff; r?cthulhu:public

Bad Merge (using the now obsolete inline-patch created earlier)

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p4 inbound http://localhost:9898 --push-bookmark "bookmark" --patch-file $TESTTMP/patch
  (200, u'{\n  "request_id": 7\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 7 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "We\'re sorry, Autoland could not rebase your commits for you automatically. Please manually rebase your commits and try again.*}') (glob)

Create a commit to test on Try

  $ echo try > foo
  $ hg commit -m 'Bug 1 - some stuff; r?cthulhu'
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/57879a256630*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 6 changesets for review
  
  changeset:  0:4b444b4e2552
  summary:    Bug 1 - some stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  1:51664e0c33c2
  summary:    Bug 1 - some more stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  changeset:  2:3c9a0891b189
  summary:    Bug 1 - even more stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/5 (draft)
  
  changeset:  3:a5988e16f939
  summary:    Bug 1 - more goodness; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/6 (draft)
  
  changeset:  4:c0f22d03c452
  summary:    Bug 1 - ?????; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  5:17f2b94883c2
  summary:    Bug 1 - some stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/7 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)
  $ REV=`hg log -r . --template "{node|short}"`

Post a job with try syntax

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p8 try http://localhost:9898 --trysyntax "stuff" --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (400, u'{\n  "error": "Bad request: trysyntax is not supported with patch_urls"\n}')

Getting status for an unknown job should return a 404

  $ ottoland autoland-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

Ensure unexpected files in the repo path are not landed.

  $ mozreview exec autoland touch /repos/test-repo/rogue
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p9 inbound http://localhost:9898 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 8\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 8 --poll
  (200, u'{\n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "patch_urls": [\n    "http://$DOCKER_HOSTNAME:$HGPORT/test-repo/raw-rev/17f2b94883c2"\n  ], \n  "result": "cfc8ffd8ebfa7c3ea28188ea5a79fd1845203791", \n  "rev": "p9", \n  "tree": "test-repo"\n}')
  $ mozreview exec autoland hg files --cwd /repos/test-repo
  foo

Test pingback url whitelist.  localhost, private IPs, and example.com are in
the whitelist. example.org is not.

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p10 inbound http://example.com:9898 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 9\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p11 inbound http://localhost --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 10\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p12 inbound http://localhost --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 11\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p13 inbound http://127.0.0.1 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 12\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p14 inbound http://192.168.0.1 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 13\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p15 inbound http://172.16.0.1 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 14\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p16 inbound http://10.0.0.1:443 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (200, u'{\n  "request_id": 15\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p17 inbound http://8.8.8.8:443 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (400, u'{\n  "error": "Bad request: bad pingback_url"\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p18 inbound http://example.org:9898 --patch-url ${MERCURIAL_URL}test-repo/raw-rev/$REV
  (400, u'{\n  "error": "Bad request: bad pingback_url"\n}')

Post the same job twice.  Start with stopping the autoland service to
guarentee the first request is still in the queue when the second is submitted.

  $ PID=`mozreview exec autoland ps x | grep autoland.py | grep -v grep | awk '{ print $1 }'`
  $ mozreview exec autoland kill $PID
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p19 inbound http://localhost:9898 --trysyntax "stuff"
  (200, u'{\n  "request_id": 16\n}')
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo p19 inbound http://localhost:9898 --trysyntax "stuff"
  (400, u'{\n  "error": "Bad Request: a request to land revision p19 to inbound is already in progress"\n}')

  $ mozreview stop
  stopped 9 containers
