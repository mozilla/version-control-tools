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
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/737709d9e5f4*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  abort: invalid Bugzilla username/password; check your settings
  [255]

Pushing with invalid password results in sane failure

  $ hg --config bugzilla.username=${BUGZILLA_USERNAME} --config bugzilla.password=badpass push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: invalid Bugzilla username/password; check your settings
  [255]

Pushing with invalid cookie results in sane failure

  $ hg --config bugzilla.userid=baduserid --config bugzilla.cookie=irrelevant push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
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
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/goodcookie
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

Pushing using username password auth works

  $ hg --config bugzilla.username=${BUGZILLA_USERNAME} --config bugzilla.password=${BUGZILLA_PASSWORD} push --reviewid bz://1/gooduserpass
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/4 (draft) (glob)
  
  review id:  bz://1/gooduserpass
  review url: http://*:$HGPORT1/r/3 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

Pushing as a user not in Review Board should auto create the RB account
We create 2 users here. 1 looks like a normal person: "First Last"
The other has Mozilla IRC syntax: "First Last [:nick]"

  $ adminbugzilla create-user user1@example.com password1 'Dummy User1'
  created user 6
  $ mozreview create-ldap-user user1@example.com user1 2001 'User One' --key-file ${MOZREVIEW_HOME}/keys/user1@example.com --scm-level 1
  $ adminbugzilla create-user user2@example.com password2 'Mozila User [:nick]'
  created user 7
  $ mozreview create-ldap-user user2@example.com user2 2002 'User Two' --key-file ${MOZREVIEW_HOME}/keys/user2@example.com --scm-level 1

  $ exportbzauth user1@example.com password1
  $ hg push --reviewid bz://1/nonick
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/6 (draft) (glob)
  
  review id:  bz://1/nonick
  review url: http://*:$HGPORT1/r/5 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

  $ exportbzauth user2@example.com password2
  $ hg push --reviewid bz://1/withnick
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/8 (draft) (glob)
  
  review id:  bz://1/withnick
  review url: http://*:$HGPORT1/r/7 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

Usernames for users without the IRC nick syntax are based on email fragment and BZ user id

  $ exportbzauth user1@example.com password1
  $ rbmanage dump-user 'user1+6'
  4:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user1@example.com
    first_name: Dummy User1
    fullname: Dummy User1
    id: 4
    last_name: ''
    url: /users/user1%2B6/
    username: user1+6

Newly created users should have a suitable profile (e.g. is_private is set)

  $ rbmanage dump-account-profile 'user1+6'
  collapsed_diffs: 1
  dashboard_columns: 
  default_use_rich_text: None
  extra_data: {}
  first_time_setup_done: 0
  group_columns: 
  id: 2
  is_private: 1
  open_an_issue: 1
  review_request_columns: 
  should_send_email: 1
  should_send_own_updates: 1
  show_closed: 1
  sort_dashboard_columns: 
  sort_group_columns: 
  sort_review_request_columns: 
  sort_submitter_columns: 
  submitter_columns: 
  syntax_highlighting: 1
  timezone: UTC
  user_id: 4
  wordwrapped_diffs: 1

Usernames for users with IRC nicks are the IRC nickname

  $ exportbzauth user2@example.com password2
  $ rbmanage dump-user nick
  5:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2@example.com
    first_name: Mozila User [:nick]
    fullname: Mozila User [:nick]
    id: 5
    last_name: ''
    url: /users/nick/
    username: nick

Changing the IRC nickname in Bugzilla will update the RB username

  $ adminbugzilla update-user-fullname user2@example.com 'Mozilla User [:newnick]'
  updated user 7

  $ exportbzauth user2@example.com password2
  $ hg push --reviewid bz://1/user2newnick
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/10 (draft) (glob)
  
  review id:  bz://1/user2newnick
  review url: http://*:$HGPORT1/r/9 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

  $ rbmanage dump-user newnick
  5:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 5
    last_name: ''
    url: /users/newnick/
    username: newnick

Changing the email address in Bugzilla will update the RB email

  $ adminbugzilla update-user-email user2@example.com user2-new@example.com
  updated user 7
  $ exportbzauth user2-new@example.com password2
  $ SSH_KEYNAME=user2@example.com hg push --reviewid bz://1/user2newemail
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/12 (draft) (glob)
  
  review id:  bz://1/user2newemail
  review url: http://*:$HGPORT1/r/11 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

  $ rbmanage dump-user newnick
  5:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 5
    last_name: ''
    url: /users/newnick/
    username: newnick

Disabling a user in Bugzilla will prevent them from using Review Board

  $ adminbugzilla update-user-login-denied-text user1@example.com disabled
  updated user 6

(This error message isn't terrific. It can be improved later.)
  $ exportbzauth user1@example.com
  $ hg --config bugzilla.username=user1@example.com --config bugzilla.password=password1 push --reviewid bz://1/disableduser
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: invalid Bugzilla username/password; check your settings
  [255]

Re-enabling a disabled user will allow them to use Review Board

  $ adminbugzilla update-user-login-denied-text user1@example.com ''
  updated user 6
  $ exportbzauth user1@example.com password1
  $ hg push --reviewid bz://1/undisableduser
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/14 (draft) (glob)
  
  review id:  bz://1/undisableduser
  review url: http://*:$HGPORT1/r/13 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

If a new Review Board user claims the same IRC nick as an existing user,
we fall back to non-IRC RB usernames.

  $ adminbugzilla create-user user3@example.com password3 'Dummy User3 [:newnick]'
  created user 8
  $ mozreview create-ldap-user user3@example.com user3 2003 'User Three' --key-file ${MOZREVIEW_HOME}/keys/user3@example.com --scm-level 1

  $ exportbzauth user3@example.com password3
  $ hg push --reviewid bz://1/conflictingircnick
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/16 (draft) (glob)
  
  review id:  bz://1/conflictingircnick
  review url: http://*:$HGPORT1/r/15 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

(Recycling user2 for this test is a bit dangerous. We should consider
adding a new user or splitting this test file.)

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user newnick
  5:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 5
    last_name: ''
    url: /users/newnick/
    username: newnick

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user user3+8
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Dummy User3 [:newnick]
    fullname: Dummy User3 [:newnick]
    id: 6
    last_name: ''
    url: /users/user3%2B8/
    username: user3+8

If an existing RB user changes their IRC nick to one taken by another RB
user, they will be assigned the email+id username.

  $ adminbugzilla update-user-fullname user3@example.com 'Mozilla User3 [:mynick]'
  updated user 8

(We need to push to get the RB username updated)

  $ exportbzauth user3@example.com password3
  $ hg push --reviewid bz://1/user3newnick > /dev/null
  [1]

  $ rbmanage dump-user mynick
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Mozilla User3 [:mynick]
    fullname: Mozilla User3 [:mynick]
    id: 6
    last_name: ''
    url: /users/mynick/
    username: mynick

(Now update another RB user to have :newnick)

(But first we check the existing state, just in case tests change)

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user newnick
  5:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 5
    last_name: ''
    url: /users/newnick/
    username: newnick

  $ adminbugzilla update-user-fullname user2-new@example.com 'Mozilla User [:mynick]'
  updated user 7

  $ exportbzauth user2-new@example.com password2
  $ SSH_KEYNAME=user2@example.com hg push --reviewid bz://1/user2sharednick
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/20 (draft) (glob)
  
  review id:  bz://1/user2sharednick
  review url: http://*:$HGPORT1/r/19 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish this series)
  [1]

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user mynick
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Mozilla User3 [:mynick]
    fullname: Mozilla User3 [:mynick]
    id: 6
    last_name: ''
    url: /users/mynick/
    username: mynick

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user user2-new+7
  5:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:mynick]
    fullname: Mozilla User [:mynick]
    id: 5
    last_name: ''
    url: /users/user2-new%2B7/
    username: user2-new+7

Cleanup

  $ mozreview stop
  stopped 8 containers
