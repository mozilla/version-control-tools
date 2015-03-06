#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Create some users

  $ adminbugzilla create-user joe1@example.com password 'Joe Smith'
  created user 6
  $ adminbugzilla create-user the-real-j-o-e@example.com password 'Joe Another'
  created user 7
  $ adminbugzilla create-user jane@example.com password 'Jane Jones [:jenny]'
  created user 8

Unauthenticated users should not be able to search

  $ BUGZILLA_USERNAME= BUGZILLA_PASSWORD= rbmanage get-users $HGPORT1 joe
  API Error: 500: 226: Bugzilla error: Logged-out users cannot use the "match" argument to this function to access any user information.
  [1]

  $ export BUGZILLA_USERNAME=joe1@example.com
  $ export BUGZILLA_PASSWORD=password

Searching with content that doesn't exist should get nothing

  $ rbmanage get-users $HGPORT1 adam
  []

An empty query string should not cause database population
(but we still get the user who initiated the query)

  $ rbmanage get-users $HGPORT1 ''
  - id: 1
    url: /users/joe1%2B6/
    username: joe1+6

Searching lowercase and uppercase versions of names returns the same
results

  $ rbmanage get-users $HGPORT1 joe
  - id: 1
    url: /users/joe1%2B6/
    username: joe1+6
  - id: 2
    url: /users/the-real-j-o-e%2B7/
    username: the-real-j-o-e+7
  $ rbmanage get-users $HGPORT1 Joe
  - id: 1
    url: /users/joe1%2B6/
    username: joe1+6
  - id: 2
    url: /users/the-real-j-o-e%2B7/
    username: the-real-j-o-e+7

Searching a full name returns results

  $ rbmanage get-users $HGPORT1 'Joe Smith'
  - id: 1
    url: /users/joe1%2B6/
    username: joe1+6

Searching a last name returns results

  $ rbmanage get-users $HGPORT1 Smith
  - id: 1
    url: /users/joe1%2B6/
    username: joe1+6

Searching an IRC nick without : returns results

  $ rbmanage get-users $HGPORT1 jenny
  - id: 3
    url: /users/jenny/
    username: jenny

Searching an IRC nick fragment returns results

  $ rbmanage get-users $HGPORT1 :jenn
  - id: 3
    url: /users/jenny/
    username: jenny

Searching an IRC nick with : prefix returns results

  $ rbmanage get-users $HGPORT1 :jenny
  - id: 3
    url: /users/jenny/
    username: jenny

Searching on name for a user with IRC nick returns results

  $ rbmanage get-users $HGPORT1 Jane
  - id: 3
    url: /users/jenny/
    username: jenny

  $ rbmanage get-users $HGPORT1 'Jane Jones'
  - id: 3
    url: /users/jenny/
    username: jenny

Cleanup

  $ mozreview stop
  stopped 5 containers
