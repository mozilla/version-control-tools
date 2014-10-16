#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh

  $ commonenv rb-test-auth

  $ cd client
  $ echo foo0 > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .
  $ hg push --noreview > /dev/null
  $ echo foo1 > foo
  $ hg commit -m 'Bug 1 - Testing 1 2 3'

  $ bugzilla create-bug TestProduct TestComponent bug1

Pushing with unknown username results in sane failure

  $ hg --config bugzilla.username=unknown --config bugzilla.password=irrelevant push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 1 changesets for review
  abort: invalid Bugzilla username/password; check your settings
  [255]

Pushing with invalid password results in sane failure

  $ hg --config bugzilla.username=${BUGZILLA_USERNAME} --config bugzilla.password=badpass push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: invalid Bugzilla username/password; check your settings
  [255]

Pushing with invalid cookie results in sane failure

  $ hg --config bugzilla.userid=baduserid --config bugzilla.cookie=irrelevant push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: invalid Bugzilla login cookie; is it expired?
  [255]

Pushing using cookie auth works

  $ out=`bugzilla create-login-cookie`
  $ userid=`echo ${out} | awk '{print $1}'`
  $ cookie=`echo ${out} | awk '{print $2}'`

  $ hg --config bugzilla.userid=${userid} --config bugzilla.cookie=${cookie} push --reviewid bz://1/goodcookie
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://1/goodcookie
  review url: http://localhost:$HGPORT1/r/1 (pending)
  [1]

Pushing using username password auth works

  $ hg --config bugzilla.username=${BUGZILLA_USERNAME} --config bugzilla.password=${BUGZILLA_PASSWORD} push --reviewid bz://1/gooduserpass
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  review id:  bz://1/gooduserpass
  review url: http://localhost:$HGPORT1/r/3 (pending)
  [1]

Pushing as a user not in Review Board should auto create the RB account
We create 2 users here. 1 looks like a normal person: "First Last"
The other has Mozilla IRC syntax: "First Last [:nick]"

  $ $TESTDIR/testing/bugzilla.py create-user user1@example.com password1 'Dummy User1'
  created user 2
  $ $TESTDIR/testing/bugzilla.py create-user user2@example.com password2 'Mozila User [:nick]'
  created user 3

  $ hg --config bugzilla.username=user1@example.com --config bugzilla.password=password1 push --reviewid bz://1/nonick
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/6 (pending)
  
  review id:  bz://1/nonick
  review url: http://localhost:$HGPORT1/r/5 (pending)
  [1]

  $ hg --config bugzilla.username=user2@example.com --config bugzilla.password=password2 push --reviewid bz://1/withnick
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/8 (pending)
  
  review id:  bz://1/withnick
  review url: http://localhost:$HGPORT1/r/7 (pending)
  [1]

Usernames for users without the IRC nick syntax are based on email fragment and BZ user id

  $ rbmanage ../rbserver dump-user $HGPORT1 'user1+2'
  2:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user1@example.com
    first_name: Dummy User1
    fullname: Dummy User1
    id: 2
    last_name: ''
    url: /users/user1%2B2/
    username: user1+2

Usernames for users with IRC nicks are the IRC nickname

  $ rbmanage ../rbserver dump-user $HGPORT1 nick
  3:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2@example.com
    first_name: Mozila User [:nick]
    fullname: Mozila User [:nick]
    id: 3
    last_name: ''
    url: /users/nick/
    username: nick

Cleanup

  $ rbmanage ../rbserver stop
  $ $TESTDIR/testing/docker-control.py stop-bmo rb-test-auth > /dev/null
