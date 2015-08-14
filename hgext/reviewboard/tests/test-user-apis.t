#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Create some users

  $ mozreview create-user joe1@example.com password 'Joe Smith'
  Created user 6
  $ mozreview create-user the-real-j-o-e@example.com password 'Joe Another' --no-api-key
  Created user 7
  $ mozreview create-user jane@example.com password 'Jane Jones [:jenny]' --no-api-key
  Created user 8
  $ mozreview create-user john.mclane@example.com password 'John McLane' --no-api-key
  Created user 9
  $ mozreview create-user sarah.connor@example.com password 'Sarah Connor' --no-api-key
  Created user 10

Unauthenticated users should not be able to search

  $ BUGZILLA_USERNAME= BUGZILLA_PASSWORD= rbmanage get-users joe
  API Error: 500: 226: Bugzilla error: There is no Bugzilla API key on record for this user. Please log into MozReview's UI to have one generated.
  [1]

  $ exportbzauth joe1@example.com password

Searching with content that doesn't exist should get nothing

  $ rbmanage get-users adam
  []

An empty query string should not cause database population
(but we still get the user who initiated the query)

  $ rbmanage get-users ''
  - id: 1
    url: /users/admin%2B1/
    username: admin+1
  - id: 3
    url: /users/default%2B5/
    username: default+5
  - id: 4
    url: /users/joe1%2B6/
    username: joe1+6
  - id: 2
    url: /users/mozreview/
    username: mozreview

Searching lowercase and uppercase versions of names returns the same
results. Also, users without :ircnick syntax won't get populated via
search.

  $ rbmanage get-users joe
  - id: 4
    url: /users/joe1%2B6/
    username: joe1+6
  $ rbmanage get-users Joe
  - id: 4
    url: /users/joe1%2B6/
    username: joe1+6

Searching a full name returns results

  $ rbmanage get-users 'Joe Smith'
  - id: 4
    url: /users/joe1%2B6/
    username: joe1+6

Searching a last name returns results

  $ rbmanage get-users Smith
  - id: 4
    url: /users/joe1%2B6/
    username: joe1+6

Searching an IRC nick without : returns results

  $ rbmanage get-users jenny
  - id: 5
    url: /users/jenny/
    username: jenny

Searching an IRC nick fragment returns results

  $ rbmanage get-users :jenn
  - id: 5
    url: /users/jenny/
    username: jenny

Searching an IRC nick with : prefix returns results

  $ rbmanage get-users :jenny
  - id: 5
    url: /users/jenny/
    username: jenny

Searching on name for a user with IRC nick returns results

  $ rbmanage get-users Jane
  - id: 5
    url: /users/jenny/
    username: jenny

  $ rbmanage get-users 'Jane Jones'
  - id: 5
    url: /users/jenny/
    username: jenny

A search on an exact name match will populate the user

  $ rbmanage get-users 'John McLane'
  - id: 6
    url: /users/john.mclane%2B9/
    username: john.mclane+9

A search on an exact email match will populate the user

  $ rbmanage get-users sarah.connor@example.com
  - id: 7
    url: /users/sarah.connor%2B10/
    username: sarah.connor+10

Cleanup

  $ mozreview stop
  stopped 8 containers
