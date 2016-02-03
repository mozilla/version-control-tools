#require mozreviewdocker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv
  $ apikey=`mozreview create-api-key ${BUGZILLA_USERNAME}`

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > reviewboard = $TESTDIR/hgext/reviewboard/client.py
  > [reviewboard]
  > fakeids = true
  > autopublish = false
  > [ui]
  > ssh = $TESTDIR/testing/mozreview-ssh
  > [mozilla]
  > ircnick = dummy
  > [bugzilla]
  > username = ${BUGZILLA_USERNAME}
  > apikey = ${apikey}
  > EOF


  $ bugzilla create-bug TestProduct TestComponent bug1

  $ export PUSHPREFIX=ssh://${HGSSH_HOST}:${HGSSH_PORT}

Create some repositories to discover from

  $ mozreview create-repo a
  HTTP URL (read only): http://$DOCKER_HOSTNAME:$HGPORT/a
  SSH URL (read+write): ssh://$DOCKER_HOSTNAME:$HGPORT6/a
  
  Run the following to create a configured clone:
    ./mozreview clone a /path/to/clone
  
  And a clone bound to a particular user:
    ./mozreview clone a /path/to/clone --user <user>
  $ mozreview create-repo b
  HTTP URL (read only): http://$DOCKER_HOSTNAME:$HGPORT/b
  SSH URL (read+write): ssh://$DOCKER_HOSTNAME:$HGPORT6/b
  
  Run the following to create a configured clone:
    ./mozreview clone b /path/to/clone
  
  And a clone bound to a particular user:
    ./mozreview clone b /path/to/clone --user <user>

  $ mkdir repos
  $ cd repos
The sleep here patches over an apparent race condition. It is a hacky
workaround to an unidentified root problem.
  $ sleep 1
  $ hg -q clone ${MERCURIAL_URL}a
  $ cd a
  $ echo foo > foo
  $ hg -q commit -A -m 'Repo a initial'
  $ hg phase --public -r .
  $ hg push --noreview ${PUSHPREFIX}/a
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/a
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ hg log -r 0 -T '{node}\n'
  4016108b6e06add4c0ddde40dee8c7b9aa410f58
  $ cd ..

  $ hg -q clone ${MERCURIAL_URL}b
  $ cd b
  $ echo foo > foo
  $ hg -q commit -A -m 'Repo b initial'
  $ hg phase --public -r .

  $ hg push --noreview ${PUSHPREFIX}/b
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/b
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ hg log -r 0 -T '{node}\n'
  36d47cf7c6cbd312de3aeb3b2f770c650b014053
  $ cd ../..

hg createrepomanifest will create and print a manifest of review repos

  $ mozreview exec hgrb /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/autoreview createrepomanifest ${MERCURIAL_URL} ${PUSHPREFIX}/
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 http://$DOCKER_HOSTNAME:$HGPORT/b ssh://$DOCKER_HOSTNAME:$HGPORT6/b
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 http://$DOCKER_HOSTNAME:$HGPORT/a ssh://$DOCKER_HOSTNAME:$HGPORT6/a

createrepomanifest should have created a file

  $ mozreview exec hgrb cat /repo/hg/mozilla/autoreview/.hg/reviewrepos
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 http://$DOCKER_HOSTNAME:$HGPORT/b ssh://$DOCKER_HOSTNAME:$HGPORT6/b
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 http://$DOCKER_HOSTNAME:$HGPORT/a ssh://$DOCKER_HOSTNAME:$HGPORT6/a

repo list accessible via JSON API

  $ http --no-headers ${MERCURIAL_URL}autoreview/json-mozreviewreviewrepos
  200
  
  {
    "36d47cf7c6cbd312de3aeb3b2f770c650b014053": "http://$DOCKER_HOSTNAME:$HGPORT/b ssh://$DOCKER_HOSTNAME:$HGPORT6/b", 
    "4016108b6e06add4c0ddde40dee8c7b9aa410f58": "http://$DOCKER_HOSTNAME:$HGPORT/a ssh://$DOCKER_HOSTNAME:$HGPORT6/a"
  }


Pushing a repository unrelated to any known repo should result in error message

  $ hg init unrelated
  $ cd unrelated
  $ echo unrelated > foo
  $ hg -q commit -A -m 'Bug 1 - Unrelated repo'
  $ hg push ${PUSHPREFIX}/autoreview
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/autoreview
  searching for appropriate review repository
  abort: no review repository found
  [255]

  $ cd ..

Pushing to autodiscover repo should redirect

  $ hg -q clone ${MERCURIAL_URL}a
  $ cd a
  $ echo discovery > foo
  $ hg commit -m 'Bug 1 - Testing discovery of a'
  $ hg push ${PUSHPREFIX}/autoreview
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/autoreview
  searching for appropriate review repository
  redirecting push to ssh://$DOCKER_HOSTNAME:$HGPORT6/a
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/a/.hg/strip-backup/e55631d0cc1a*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:daa176714e3a
  summary:    Bug 1 - Testing discovery of a
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/dummy
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

  $ cd ..

Redirecting to different hostname should be disallowed (security protection)

  $ mozreview exec hgrb /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/autoreview createrepomanifest ${MERCURIAL_URL} ssh://bad.host/
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 http://$DOCKER_HOSTNAME:$HGPORT/b ssh://bad.host/b
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 http://$DOCKER_HOSTNAME:$HGPORT/a ssh://bad.host/a

  $ hg -q clone ${MERCURIAL_URL}b
  $ cd b
  $ echo bad_redirect > foo
  $ hg commit -m 'Bug 1 - Testing discovery of b'
  $ hg push ${PUSHPREFIX}/autoreview
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/autoreview
  searching for appropriate review repository
  abort: refusing to redirect due to URL mismatch: ssh://bad.host/b
  [255]

  $ cd ..

Redirecting works when pushing over HTTP

  $ mozreview exec hgrb /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/autoreview createrepomanifest ${MERCURIAL_URL} ${PUSHPREFIX}/
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 http://$DOCKER_HOSTNAME:$HGPORT/b ssh://$DOCKER_HOSTNAME:$HGPORT6/b
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 http://$DOCKER_HOSTNAME:$HGPORT/a ssh://$DOCKER_HOSTNAME:$HGPORT6/a

  $ hg -q clone ${MERCURIAL_URL}a http-redirect
  $ cd http-redirect
  $ echo http_redirect > foo
  $ hg commit -m 'Bug 1 - Testing discovery via HTTP pushes'
  $ hg --config mozilla.trustedbmoapikeyservices=${MERCURIAL_URL} push ${MERCURIAL_URL}autoreview -c .
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/autoreview
  searching for appropriate review repository
  redirecting push to http://$DOCKER_HOSTNAME:$HGPORT/a
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/http-redirect/.hg/strip-backup/5f3de01b6263-bb45f39e-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  2:e94691c71b1a
  summary:    Bug 1 - Testing discovery via HTTP pushes
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/dummy
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

Pushing to autoreview repo without client extension results in sane failure
(Test with both SSH and HTTP because peer handling of errors is
different)

  $ hg --config extensions.reviewboard=! push ${PUSHPREFIX}/autoreview
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/autoreview
  remote: 
  remote: Pushing and pull review discovery repos is not allowed!
  remote: 
  remote: You are likely seeing this error because:
  remote: 
  remote: 1) You do not have the appropriate Mercurial extension installed
  remote: 2) The extension is out of date
  remote: 
  remote: See https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html
  remote: for instructions on how to configure your machine to use MozReview.
  remote: 
  remote: -
  abort: remote error
  (check previous remote output)
  [255]

  $ cat >> .hg/hgrc << EOF
  > [auth]
  > t.prefix = ${MERCURIAL_URL}
  > t.username = ${BUGZILLA_USERNAME}
  > t.password = ${apikey}
  > EOF

  $ hg --config extensions.reviewboard=! --config mozilla.trustedbmoapikeyservices=${MERCURIAL_URL} push ${MERCURIAL_URL}autoreview
  pushing to http://$DOCKER_HOSTNAME:$HGPORT/autoreview
  abort: remote error:
  
  Pushing and pull review discovery repos is not allowed!
  
  You are likely seeing this error because:
  
  1) You do not have the appropriate Mercurial extension installed
  2) The extension is out of date
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html
  for instructions on how to configure your machine to use MozReview.
  [255]

Pulling from autoreview repos also error
(although we don't expect to see this much in the wild)

  $ hg --config extensions.reviewboard=! pull ${PUSHPREFIX}/autoreview
  pulling from ssh://$DOCKER_HOSTNAME:$HGPORT6/autoreview
  remote: 
  remote: Pushing and pull review discovery repos is not allowed!
  remote: 
  remote: You are likely seeing this error because:
  remote: 
  remote: 1) You do not have the appropriate Mercurial extension installed
  remote: 2) The extension is out of date
  remote: 
  remote: See https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html
  remote: for instructions on how to configure your machine to use MozReview.
  remote: 
  remote: -
  abort: remote error
  (check previous remote output)
  [255]

  $ hg --config extensions.reviewboard=! --config mozilla.trustedbmoapikeyservices=${MERCURIAL_URL} pull ${MERCURIAL_URL}autoreview
  pulling from http://$DOCKER_HOSTNAME:$HGPORT/autoreview
  abort: remote error:
  
  Pushing and pull review discovery repos is not allowed!
  
  You are likely seeing this error because:
  
  1) You do not have the appropriate Mercurial extension installed
  2) The extension is out of date
  
  See https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html
  for instructions on how to configure your machine to use MozReview.
  [255]

  $ cd ..

Cleanup

  $ mozreview stop
  stopped 9 containers
