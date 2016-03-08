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

Ensure Autoland started without errors

  $ mozreview exec autoland tail -n 20 /home/ubuntu/autoland.log
  * autoland INFO starting autoland (glob)

Posting a job with bad credentials should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898 --user blah --password blah
  (401, u'Login required')

Posting a job with without both trysyntax and commit_descriptions should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo 42 try http://localhost:9898
  (400, u'{\n  "error": "Bad request: one of trysyntax or commit_descriptions must be specified."\n}')

Posting a job with an unknown revision should fail

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo 42 try http://localhost:9898 --commit-descriptions "{\"42\": \"bad revision\"}"
  (200, u'{\n  "request_id": 1\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 1 --poll
  (200, u'{\n  "commit_descriptions": {\n    "42": "bad revision"\n  }, \n  "destination": "try", \n  "error_msg": "hg error in cmd: hg pull test-repo -r 42: pulling from http://hgrb/test-repo\\nabort: unknown revision \'42\'!\\n", \n  "landed": false, \n  "ldap_username": "autolanduser@example.com", \n  "push_bookmark": "", \n  "result": "", \n  "rev": "42", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')

Post a job

  $ REV=`hg log -r . --template "{node|short}"`
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo $REV inbound http://localhost:9898 --commit-descriptions "{\"$REV\": \"Bug 1 - some stuff; r=cthulhu\"}"
  (200, u'{\n  "request_id": 2\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 2 --poll
  (200, u'{\n  "commit_descriptions": {\n    "e2507be7827c": "Bug 1 - some stuff; r=cthulhu"\n  }, \n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "push_bookmark": "", \n  "result": "3bce87fd55d0", \n  "rev": "e2507be7827c", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')
  $ mozreview exec autoland hg log /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  0:Bug 1 - some stuff; r=cthulhu:public

Post a job with try syntax

  $ ottoland post-autoland-job $AUTOLAND_URL test-repo `hg log -r . --template "{node|short}"` try http://localhost:9898 --trysyntax "stuff"
  (200, u'{\n  "request_id": 3\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 3 --poll
  (200, u'{\n  "commit_descriptions": "", \n  "destination": "try", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "push_bookmark": "", \n  "result": "*", \n  "rev": "e2507be7827c", \n  "tree": "test-repo", \n  "trysyntax": "stuff"\n}') (glob)
  $ mozreview exec autoland hg log /repos/try/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  2:try: stuff:draft
  1:Bug 1 - some stuff; r?cthulhu:draft
  0:root commit:public

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
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo $REV inbound http://localhost:9898 --push-bookmark "bookmark" --commit-descriptions "{\"$REV\": \"Bug 1 - more goodness; r=cthulhu\"}"
  (200, u'{\n  "request_id": 4\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 4 --poll
  (200, u'{\n  "commit_descriptions": {\n    "373b6ff60965": "Bug 1 - more goodness; r=cthulhu"\n  }, \n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "push_bookmark": "bookmark", \n  "result": "aba7cf08f2e4", \n  "rev": "373b6ff60965", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')
  $ mozreview exec autoland hg log /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  1:Bug 1 - more goodness; r=cthulhu:public
  0:Bug 1 - some stuff; r=cthulhu:public

Post a job with unicode commit descriptions to be rewritten

  $ echo foo3 > foo
  $ hg commit --encoding utf-8 -m 'Bug 1 - こんにちは; r?cthulhu'
  $ hg push --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 3 changesets for review
  
  changeset:  1:e2507be7827c
  summary:    Bug 1 - some stuff; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  changeset:  2:373b6ff60965
  summary:    Bug 1 - more goodness; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/3 (draft)
  
  changeset:  3:e7f4a0f07be3
  summary:    Bug 1 - ?????; r?cthulhu
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/4 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (visit review url to publish these review requests so others can see them)
  $ REV=`hg log -r . --template "{node|short}"`
  $ ottoland post-autoland-job $AUTOLAND_URL test-repo $REV inbound http://localhost:9898 --commit-descriptions "{\"$REV\": \"Bug 1 - \\u3053\\u3093\\u306b\\u3061\\u306f; r=cthulhu\"}"
  (200, u'{\n  "request_id": 5\n}')
  $ ottoland autoland-job-status $AUTOLAND_URL 5 --poll
  (200, u'{\n  "commit_descriptions": {\n    "e7f4a0f07be3": "Bug 1 - \\u3053\\u3093\\u306b\\u3061\\u306f; r=cthulhu"\n  }, \n  "destination": "inbound", \n  "error_msg": "", \n  "landed": true, \n  "ldap_username": "autolanduser@example.com", \n  "push_bookmark": "", \n  "result": "8ec6d9d32147", \n  "rev": "e7f4a0f07be3", \n  "tree": "test-repo", \n  "trysyntax": ""\n}')

  $ mozreview exec autoland hg log --encoding=utf-8 /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  2:Bug 1 - \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf; r=cthulhu:public (esc)
  1:Bug 1 - more goodness; r=cthulhu:public
  0:Bug 1 - some stuff; r=cthulhu:public

Getting status for an unknown job should return a 404

  $ ottoland autoland-job-status $AUTOLAND_URL 42
  (404, u'{\n  "error": "Not found"\n}')

  $ mozreview exec autoland hg log --encoding=utf-8 /repos/test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  3:Bug 1 - \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf; r=cthulhu:public (esc)
  2:Bug 1 - more goodness; r=cthulhu:public
  1:Bug 1 - some stuff; r=cthulhu:public
  0:root commit:public

  $ mozreview exec autoland hg log /repos/try/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  2:try: stuff:draft
  1:Bug 1 - some stuff; r?cthulhu:draft
  0:root commit:public

  $ mozreview exec autoland hg log --encoding=utf-8 /repos/inbound-test-repo/ --template '{rev}:{desc\|firstline}:{phase}\\n'
  2:Bug 1 - \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf; r=cthulhu:public (esc)
  1:Bug 1 - more goodness; r=cthulhu:public
  0:Bug 1 - some stuff; r=cthulhu:public

  $ mozreview stop
  stopped 9 containers
