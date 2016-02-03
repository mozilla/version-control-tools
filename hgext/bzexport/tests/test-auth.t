#require bmodocker
  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh

  $ $TESTDIR/d0cker start-bmo bzexport-test-auth $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://$DOCKER_HOSTNAME:$HGPORT/

  $ export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT/

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > mq =
  > bzexport = $TESTDIR/hgext/bzexport
  > 
  > [bzexport]
  > bugzilla = ${BUGZILLA_URL}
  > EOF

Dummy out profiles directory to prevent running system from leaking in

  $ export FIREFOX_PROFILES_DIR=`pwd`

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg -q commit -A -m initial

No auth info should lead to prompting (verifies mozhg.auth is hooked up)

  $ hg newbug --product TestProduct --component TestComponent -t 'No auth' 'dummy'
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]

bzexport.username is deprecated and should print a warning

  $ hg --config bzexport.username=olduser newbug --product TestProduct --component TestComponent -t 'old username' 'dummy'
  (the bzexport.username config option is deprecated and ignored; use bugzilla.username instead)
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]

bzexport.password is deprecated and should print a warning

  $ hg --config bzexport.password=oldpass newbug --product TestProduct --component TestComponent -t 'old password' 'dummy'
  (the bzexport.password config option is deprecated and ignored; use bugzilla.password or cookie auth by logging into Bugzilla in Firefox)
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]

bzexport.api_server is deprecated and should print a warning

  $ hg --config bzexport.api_server=http://dummy/bzapi newbug --product TestProduct --component TestComponent -t 'api server' 'dummy'
  (the bzexport.api_server config option is deprecated and ignored; delete it from your config)
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]

Invalid cookie should result in appropriate error message

  $ hg --config bugzilla.userid=badid --config bugzilla.cookie=badcookie newbug --product TestProduct --component TestComponent -t 'Bad Cookie' 'dummy'
  Refreshing configuration cache for http://$DOCKER_HOSTNAME:$HGPORT/bzapi/
  Using default version 'unspecified' of product TestProduct
  abort: error creating bug: REST error on POST to http://$DOCKER_HOSTNAME:$HGPORT/rest/bug: You must log in before using this part of Bugzilla.
  [255]

  $ echo patch > foo
  $ hg qnew -d '0 0' -m 'Bug 1 - Test cookie' cookie-patch
  $ hg --config bugzilla.userid=badid --config bugzilla.cookie=badcookie bzexport
  abort: error uploading attachment: REST error on POST to http://$DOCKER_HOSTNAME:$HGPORT/rest/bug/1/attachment: You must log in before using this part of Bugzilla.
  [255]

Cookie authentication works

  $ out=`bugzilla create-login-cookie`
  $ userid=`echo ${out} | awk '{print $1}'`
  $ cookie=`echo ${out} | awk '{print $2}'`

  $ hg --config bugzilla.userid=${userid} --config bugzilla.cookie=${cookie} newbug --product TestProduct --component TestComponent -t 'Good Cookie' 'dummy'
  Using default version 'unspecified' of product TestProduct
  Created bug 1 at http://$DOCKER_HOSTNAME:$HGPORT/show_bug.cgi?id=1
  $ hg --config bugzilla.userid=${userid} --config bugzilla.cookie=${cookie} bzexport
  cookie-patch uploaded as http://$DOCKER_HOSTNAME:$HGPORT/attachment.cgi?id=1&action=edit

Bad API key results in failure

  $ hg --config bugzilla.username=user --config bugzilla.apikey=badkey newbug --product TestProduct --component TestComponen -t 'Bad Key' 'dummy'
  Using default version 'unspecified' of product TestProduct
  abort: error creating bug: REST error on POST to http://$DOCKER_HOSTNAME:$HGPORT/rest/bug: The API key you specified is invalid. Please check that you typed it correctly.
  [255]
t

Cleanup

  $ $TESTDIR/d0cker stop-bmo bzexport-test-auth
  stopped 1 containers
