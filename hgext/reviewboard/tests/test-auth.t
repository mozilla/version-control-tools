#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

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
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
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
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: invalid Bugzilla username/password; check your settings
  [255]

Pushing with invalid cookie results in sane failure

  $ hg --config bugzilla.userid=baduserid --config bugzilla.cookie=irrelevant push
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
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
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://1/goodcookie
  review url: http://localhost:$HGPORT1/r/1 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Pushing using username password auth works

  $ hg --config bugzilla.username=${BUGZILLA_USERNAME} --config bugzilla.password=${BUGZILLA_PASSWORD} push --reviewid bz://1/gooduserpass
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  review id:  bz://1/gooduserpass
  review url: http://localhost:$HGPORT1/r/3 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Pushing as a user not in Review Board should auto create the RB account
We create 2 users here. 1 looks like a normal person: "First Last"
The other has Mozilla IRC syntax: "First Last [:nick]"

  $ adminbugzilla create-user user1@example.com password1 'Dummy User1'
  created user 6
  $ adminbugzilla create-user user2@example.com password2 'Mozila User [:nick]'
  created user 7

  $ hg --config bugzilla.username=user1@example.com --config bugzilla.password=password1 push --reviewid bz://1/nonick
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/6 (pending)
  
  review id:  bz://1/nonick
  review url: http://localhost:$HGPORT1/r/5 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

  $ hg --config bugzilla.username=user2@example.com --config bugzilla.password=password2 push --reviewid bz://1/withnick
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/8 (pending)
  
  review id:  bz://1/withnick
  review url: http://localhost:$HGPORT1/r/7 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

Usernames for users without the IRC nick syntax are based on email fragment and BZ user id

  $ exportbzauth user1@example.com password1
  $ rbmanage dump-user $HGPORT1 'user1+6'
  2:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user1@example.com
    first_name: Dummy User1
    fullname: Dummy User1
    id: 2
    last_name: ''
    url: /users/user1%2B6/
    username: user1+6

Newly created users should have a suitable profile (e.g. is_private is set)

  $ rbmanage dump-account-profile 'user1+6'
  id: 2
  user_id: 2
  first_time_setup_done: 0
  should_send_email: 1
  should_send_own_updates: 1
  collapsed_diffs: 1
  wordwrapped_diffs: 1
  syntax_highlighting: 1
  is_private: 1
  open_an_issue: 1
  default_use_rich_text: None
  show_closed: 1
  sort_review_request_columns: 
  sort_dashboard_columns: 
  sort_submitter_columns: 
  sort_group_columns: 
  review_request_columns: 
  dashboard_columns: 
  submitter_columns: 
  group_columns: 
  timezone: UTC
  extra_data: {}

Usernames for users with IRC nicks are the IRC nickname

  $ exportbzauth user2@example.com password2
  $ rbmanage dump-user $HGPORT1 nick
  3:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2@example.com
    first_name: Mozila User [:nick]
    fullname: Mozila User [:nick]
    id: 3
    last_name: ''
    url: /users/nick/
    username: nick

Changing the IRC nickname in Bugzilla will update the RB username

  $ adminbugzilla update-user-fullname user2@example.com 'Mozilla User [:newnick]'
  updated user 7

  $ hg --config bugzilla.username=user2@example.com --config bugzilla.password=password2 push --reviewid bz://1/user2newnick
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/10 (pending)
  
  review id:  bz://1/user2newnick
  review url: http://localhost:$HGPORT1/r/9 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

  $ exportbzauth user2@example.com password2
  $ rbmanage dump-user $HGPORT1 newnick
  3:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 3
    last_name: ''
    url: /users/newnick/
    username: newnick

Changing the email address in Bugzilla will update the RB email

  $ adminbugzilla update-user-email user2@example.com user2-new@example.com
  updated user 7
  $ hg --config bugzilla.username=user2-new@example.com --config bugzilla.password=password2 push --reviewid bz://1/user2newemail
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/12 (pending)
  
  review id:  bz://1/user2newemail
  review url: http://localhost:$HGPORT1/r/11 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user $HGPORT1 newnick
  3:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 3
    last_name: ''
    url: /users/newnick/
    username: newnick

Disabling a user in Bugzilla will prevent them from using Review Board

  $ adminbugzilla update-user-login-denied-text user1@example.com disabled
  updated user 6

(This error message isn't terrific. It can be improved later.)
  $ hg --config bugzilla.username=user1@example.com --config bugzilla.password=password1 push --reviewid bz://1/disableduser
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: invalid Bugzilla username/password; check your settings
  [255]

Re-enabling a disabled user will allow them to use Review Board

  $ adminbugzilla update-user-login-denied-text user1@example.com ''
  updated user 6
  $ hg --config bugzilla.username=user1@example.com --config bugzilla.password=password1 push --reviewid bz://1/undisableduser
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/14 (pending)
  
  review id:  bz://1/undisableduser
  review url: http://localhost:$HGPORT1/r/13 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

If a new Review Board user claims the same IRC nick as an existing user,
we fall back to non-IRC RB usernames.

  $ adminbugzilla create-user user3@example.com password3 'Dummy User3 [:newnick]'
  created user 8

  $ hg --config bugzilla.username=user3@example.com --config bugzilla.password=password3 push --reviewid bz://1/conflictingircnick
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/16 (pending)
  
  review id:  bz://1/conflictingircnick
  review url: http://localhost:$HGPORT1/r/15 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

(Recycling user2 for this test is a bit dangerous. We should consider
adding a new user or splitting this test file.)

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user $HGPORT1 newnick
  3:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 3
    last_name: ''
    url: /users/newnick/
    username: newnick

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user $HGPORT1 user3+8
  4:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Dummy User3 [:newnick]
    fullname: Dummy User3 [:newnick]
    id: 4
    last_name: ''
    url: /users/user3%2B8/
    username: user3+8

If an existing RB user changes their IRC nick to one taken by another RB
user, they will be assigned the email+id username.

  $ adminbugzilla update-user-fullname user3@example.com 'Mozilla User3 [:mynick]'
  updated user 8

(We need to push to get the RB username updated)

  $ hg --config bugzilla.username=user3@example.com --config bugzilla.password=password3 push --reviewid bz://1/user3newnick > /dev/null
  [1]

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user $HGPORT1 mynick
  4:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Mozilla User3 [:mynick]
    fullname: Mozilla User3 [:mynick]
    id: 4
    last_name: ''
    url: /users/mynick/
    username: mynick

(Now update another RB user to have :newnick)

(But first we check the existing state, just in case tests change)

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user $HGPORT1 newnick
  3:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 3
    last_name: ''
    url: /users/newnick/
    username: newnick

  $ adminbugzilla update-user-fullname user2-new@example.com 'Mozilla User [:mynick]'
  updated user 7

  $ hg --config bugzilla.username=user2-new@example.com --config bugzilla.password=password2 push --reviewid bz://1/user2sharednick
  pushing to ssh://user@dummy/$TESTTMP/repos/test-repo
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:737709d9e5f4
  summary:    Bug 1 - Testing 1 2 3
  review:     http://localhost:$HGPORT1/r/20 (pending)
  
  review id:  bz://1/user2sharednick
  review url: http://localhost:$HGPORT1/r/19 (pending)
  (visit review url to publish this review request so others can see it)
  [1]

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user $HGPORT1 mynick
  4:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Mozilla User3 [:mynick]
    fullname: Mozilla User3 [:mynick]
    id: 4
    last_name: ''
    url: /users/mynick/
    username: mynick

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user $HGPORT1 user2-new+7
  3:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:mynick]
    fullname: Mozilla User [:mynick]
    id: 3
    last_name: ''
    url: /users/user2-new%2B7/
    username: user2-new+7

Cleanup

  $ mozreview stop
  stopped 5 containers
