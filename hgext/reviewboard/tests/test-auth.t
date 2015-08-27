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

Pushing with a password results in server rejection

  $ hg --config bugzilla.username=unknown --config bugzilla.password=irrelevant --config bugzilla.apikey= push
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
  abort: Bugzilla API keys are now used by MozReview; see https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html#bugzilla-credentials for instructions on how to configure your client
  [255]

Pushing with a cookie results in server rejection

  $ hg --config bugzilla.userid=baduserid --config bugzilla.cookie=irrelevant --config bugzilla.apikey= push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: Bugzilla API keys are now used by MozReview; see https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html#bugzilla-credentials for instructions on how to configure your client
  [255]

Pushing with unknown username with API key results in sane failure

  $ hg --config bugzilla.username=unknown --config bugzilla.apikey=irrelevant push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: Bugzilla API keys are now used by MozReview; see https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html#bugzilla-credentials for instructions on how to configure your client
  [255]

Pushing with invalid API key results in sane failure
We need to test with a new user here because the default user is already
created in Review Board.

  $ adminbugzilla create-user apikey1@example.com api1password 'API Key1'
  created user 6

  $ hg --config bugzilla.username=apikey1@example.com --config bugzilla.apikey=badkey push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: Bugzilla API keys are now used by MozReview; see https://mozilla-version-control-tools.readthedocs.org/en/latest/mozreview/install.html#bugzilla-credentials for instructions on how to configure your client
  [255]

User must log in via web interface before pushing with an API key

  $ apikey=`mozreview create-api-key apikey1@example.com`
  $ hg --config bugzilla.username=apikey1@example.com --config bugzilla.apikey=${apikey} push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: web login needed; log in at http://*:$HGPORT1/account/login then try again (glob)
  [255]

User in database without API key requires web login

  $ mozreview create-user apikey2@example.com api2password 'API Key2 [:apikey2]' --no-api-key
  Created user 7
  $ rbmanage get-users apikey2
  - id: 4
    url: /users/apikey2/
    username: apikey2
  $ apikey=`mozreview create-api-key apikey2@example.com`
  $ hg --config bugzilla.username=apikey2@example.com --config bugzilla.apikey=${apikey} push
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: web login needed; log in at http://*:$HGPORT1/account/login then try again (glob)
  [255]

Usernames for users without the IRC nick syntax are based on email fragment and BZ user id

  $ mozreview create-user user1@example.com password1 'Dummy User1' --uid 2001 --scm-level 1
  Created user 8

  $ exportbzauth user1@example.com password1
  $ rbmanage dump-user 'user1+8'
  5:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user1@example.com
    first_name: Dummy User1
    fullname: Dummy User1
    id: 5
    last_name: ''
    url: /users/user1%2B8/
    username: user1+8

Newly created users should have a suitable profile (e.g. is_private is set)

  $ rbmanage dump-account-profile 'user1+8'
  collapsed_diffs: 1
  dashboard_columns: selected,new_updates,ship_it,my_comments,summary,submitter,last_updated_since
  default_use_rich_text: None
  extra_data: {}
  first_time_setup_done: 0
  group_columns: 
  id: 4
  is_private: 1
  open_an_issue: 1
  review_request_columns: 
  should_send_email: 1
  should_send_own_updates: 1
  show_closed: 1
  sort_dashboard_columns: -last_updated
  sort_group_columns: 
  sort_review_request_columns: 
  sort_submitter_columns: 
  submitter_columns: 
  syntax_highlighting: 1
  timezone: UTC
  user_id: 5
  wordwrapped_diffs: 1

Usernames for users with IRC nicks are the IRC nickname

  $ mozreview create-user user2@example.com password2 'Mozila User [:nick]' --uid 2002 --scm-level 1
  Created user 9

  $ exportbzauth user2@example.com password2
  $ rbmanage dump-user nick
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2@example.com
    first_name: Mozila User [:nick]
    fullname: Mozila User [:nick]
    id: 6
    last_name: ''
    url: /users/nick/
    username: nick

Changing the IRC nickname in Bugzilla will update the RB username

  $ adminbugzilla update-user-fullname user2@example.com 'Mozilla User [:newnick]'
  updated user 9

  $ exportbzauth user2@example.com password2
  $ hg push --reviewid bz://1/user2newnick
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/user2newnick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish these review requests)
  [1]

  $ rbmanage dump-user newnick
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 6
    last_name: ''
    url: /users/newnick/
    username: newnick

Changing the email address in Bugzilla will update the RB email

  $ adminbugzilla update-user-email user2@example.com user2-new@example.com
  updated user 9
  $ exportbzauth user2-new@example.com password2
  $ SSH_KEYNAME=user2@example.com hg push --reviewid bz://1/user2newemail
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/4 (draft) (glob)
  
  review id:  bz://1/user2newemail
  review url: http://*:$HGPORT1/r/3 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish these review requests)
  [1]

  $ rbmanage dump-user newnick
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 6
    last_name: ''
    url: /users/newnick/
    username: newnick

Disabling a user in Bugzilla will prevent them from using Review Board

  $ adminbugzilla update-user-login-denied-text user1@example.com disabled
  updated user 8

(This error message isn't terrific. It can be improved later.)
  $ exportbzauth user1@example.com
  $ user1key=`mozreview create-api-key user1@example.com`
  $ hg --config bugzilla.username=user1@example.com --config bugzilla.apikey=${user1key} push --reviewid bz://1/disableduser
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  abort: invalid Bugzilla API key; visit Bugzilla to obtain a new API key
  [255]

Re-enabling a disabled user will allow them to use Review Board

  $ adminbugzilla update-user-login-denied-text user1@example.com ''
  updated user 8
  $ exportbzauth user1@example.com password1
  $ hg push --config bugzilla.username=user1@example.com --config bugzilla.apikey=${user1key} --reviewid bz://1/undisableduser
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  searching for changes
  no changes found
  submitting 1 changesets for review
  
  changeset:  1:d97f9c20be62
  summary:    Bug 1 - Testing 1 2 3
  review:     http://*:$HGPORT1/r/6 (draft) (glob)
  
  review id:  bz://1/undisableduser
  review url: http://*:$HGPORT1/r/5 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish these review requests)
  [1]

If a new Review Board user claims the same IRC nick as an existing user,
we fall back to non-IRC RB usernames.

  $ mozreview create-user user3@example.com password3 'Dummy User3 [:newnick]' --uid 2003 --scm-level 1
  Created user 10

(Recycling user2 for this test is a bit dangerous. We should consider
adding a new user or splitting this test file.)

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user newnick
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 6
    last_name: ''
    url: /users/newnick/
    username: newnick

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user user3+10
  7:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Dummy User3 [:newnick]
    fullname: Dummy User3 [:newnick]
    id: 7
    last_name: ''
    url: /users/user3%2B10/
    username: user3+10

If an existing RB user changes their IRC nick to one taken by another RB
user, they will be assigned the email+id username.

  $ adminbugzilla update-user-fullname user3@example.com 'Mozilla User3 [:mynick]'
  updated user 10

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user mynick
  7:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Mozilla User3 [:mynick]
    fullname: Mozilla User3 [:mynick]
    id: 7
    last_name: ''
    url: /users/mynick/
    username: mynick

(Now update another RB user to have :newnick)

(But first we check the existing state, just in case tests change)

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user newnick
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:newnick]
    fullname: Mozilla User [:newnick]
    id: 6
    last_name: ''
    url: /users/newnick/
    username: newnick

  $ adminbugzilla update-user-fullname user2-new@example.com 'Mozilla User [:mynick]'
  updated user 9

  $ exportbzauth user3@example.com password3
  $ rbmanage dump-user mynick
  7:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user3@example.com
    first_name: Mozilla User3 [:mynick]
    fullname: Mozilla User3 [:mynick]
    id: 7
    last_name: ''
    url: /users/mynick/
    username: mynick

  $ exportbzauth user2-new@example.com password2
  $ rbmanage dump-user user2-new+9
  6:
    avatar_url: http://www.gravatar.com/avatar/* (glob)
    email: user2-new@example.com
    first_name: Mozilla User [:mynick]
    fullname: Mozilla User [:mynick]
    id: 6
    last_name: ''
    url: /users/user2-new%2B9/
    username: user2-new+9

Cleanup

  $ mozreview stop
  stopped 9 containers
