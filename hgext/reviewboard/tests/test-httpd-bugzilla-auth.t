#require mozreviewdocker

  $ $TESTDIR/d0cker start-bmo httpd-bugzilla-auth $HGPORT --web-id-file web_id
  waiting for Bugzilla to start
  Bugzilla accessible on http://$DOCKER_HOSTNAME:$HGPORT/

  $ export BMOWEB_ID=`cat web_id`

  $ alias adminbugzilla='BUGZILLA_USERNAME=admin@example.com BUGZILLA_PASSWORD=password $TESTDIR/bugzilla'
  $ alias authn="python $TESTDIR/scripts/httpd-authn-bugzilla-key"

No argument raises error
  $ authn
  usage: httpd-authn-bugzilla-key [-h] [--allow-plaintext] url
  httpd-authn-bugzilla-key: error: too few arguments
  [2]

URLs must be HTTP

  $ authn file:///etc/shadow
  Bugzilla URL is not HTTP: file:///etc/shadow
  [1]

URLs must be secure unless overridden

  $ authn http://insecure.url
  Refusing to use plain text URL for security reasons: http://insecure.url
  [1]

No stdin raises error
  $ authn --allow-plaintext http://irrelevant
  Expected 2 lines on stdin; got 0
  [1]

Single line on stdin raises error

  $ authn --allow-plaintext http://irrelevant << EOF
  > username
  > EOF
  Expected 2 lines on stdin; got 1
  [1]

More than 2 lines on stdin raises error

  $ authn --allow-plaintext http://irrelevant << EOF
  > username
  > api_key
  > extra
  > EOF
  Expected 2 lines on stdin; got 3
  [1]

Actual BMO request should fail with invalid API key

  $ authn https://bugzilla.mozilla.org << EOF
  > dummy@example.com
  > api_key
  > EOF
  received HTTP status code 400; Bugzilla code 306
  [1]

Request against bad path on local server issues error

  $ export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT

  $ authn --allow-plaintext ${BUGZILLA_URL}/bad/path << EOF
  > irrelevant
  > irrelevant
  > EOF
  did not receive JSON response: text/html
  [1]

Request against local server with invalid user should fail

  $ authn --allow-plaintext ${BUGZILLA_URL} << EOF
  > invaliduser@example.com
  > irrelevant
  > EOF
  received HTTP status code 400; Bugzilla code 306
  [1]

Request against local server with valid user but invalid API key should
fail

  $ adminbugzilla create-user user1@example.com password1 'User 1'
  created user 5
  $ authn --allow-plaintext ${BUGZILLA_URL} << EOF
  > user1@example.com
  > badkey
  > EOF
  received HTTP status code 400; Bugzilla code 306
  [1]

Request against local server with valid API key but wrong user should
fail

  $ export API_KEY=`$TESTDIR/d0cker create-bugzilla-api-key ${BMOWEB_ID} user1@example.com`

  $ authn --allow-plaintext ${BUGZILLA_URL} << EOF
  > user2@example.com
  > ${API_KEY}
  > EOF
  not valid API key
  [1]

Request against local server with valid API key should work

  $ authn --allow-plaintext ${BUGZILLA_URL} << EOF
  > user1@example.com
  > ${API_KEY}
  > EOF

  $ $TESTDIR/d0cker stop-bmo httpd-bugzilla-auth
  stopped 1 containers
