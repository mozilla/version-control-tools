#require mozreviewdocker
  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ bugzilla create-bug-range TestProduct TestComponent 2
  created bugs 1 to 2

Set up repo

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ echo foo2 > foo
  $ hg commit -m 'second commit'

  $ hg phase --public -r 0

Create a user

  $ mozreview create-user user1@example.com password1 'User One [:user1]' --uid 2001 --scm-level 1
  Created user 6
  $ user1key=`mozreview create-api-key user1@example.com`
  $ exportbzauth user1@example.com password1

Dump the user so it gets mirrored over to Review Board

  $ rbmanage dump-user user1 > /dev/null

The user should not have an ldap username associated with them

  $ rbmanage dump-user-ldap user1
  no ldap username associated with user1

Perform a push with the user

  $ hg --config bugzilla.username=user1@example.com --config bugzilla.apikey=${user1key} push -r 1 --reviewid 1 --config reviewboard.autopublish=false
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT6/test-repo
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/cd3395bd3f8a*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:d5b7a3621249
  summary:    second commit
  review:     http://$DOCKER_HOSTNAME:$HGPORT1/r/2 (draft)
  
  review id:  bz://1/mynick
  review url: http://$DOCKER_HOSTNAME:$HGPORT1/r/1 (draft)
  
  (review requests lack reviewers; visit review url to assign reviewers)
  (visit review url to publish these review requests so others can see them)

The user should now have an associated ldap_username

  $ rbmanage dump-user-ldap user1
  ldap username: user1@example.com

Create another user

  $ mozreview create-user user2@example.com tastypassword 'User Two [:user2]' --uid 2001 --scm-level 1
  Created user 7
  $ user1key=`mozreview create-api-key user2@example.com`
  $ exportbzauth user2@example.com tastypassword

Dump the user so it gets mirrored over to Review Board

  $ rbmanage dump-user user2 > /dev/null

The user should not have an ldap username associated with them

  $ rbmanage dump-user-ldap user2
  no ldap username associated with user2

The user should not be able to change their own ldap email association

  $ rbmanage associate-ldap-user user2 user2@example.com --request-username=user2 --request-password=tastypassword
  API Error: 403: 101: You don't have permission for this
  [1]

The user should still have no ldap username associated with them

  $ rbmanage dump-user-ldap user2
  no ldap username associated with user2

A user without the special permission should not be able to change the association of
another user

  $ rbmanage associate-ldap-user user2 user2@example.com --request-username=user1 --request-password=password1
  API Error: 403: 101: You don't have permission for this
  [1]

The user should still have no ldap username associated with them

  $ rbmanage dump-user-ldap user2
  no ldap username associated with user2

An unauthenticated request should not be able to change an association

  $ rbmanage associate-ldap-user user2 user2@example.com --anonymous
  API Error: 401: 103: You are not logged in
  [1]

The user should still have no ldap username associated with them

  $ rbmanage dump-user-ldap user2
  no ldap username associated with user2

The special user should be able to associate the ldap account after all of
the failed attempts

  $ rbmanage associate-ldap-user user2 user2@example.com
  user2@example.com associated with user2

The user should now have an associated ldap_username

  $ rbmanage dump-user-ldap user2
  ldap username: user2@example.com

Create another user

  $ mozreview create-user user3@example.com user3password  'User Three [:user3]' --uid 2002 --scm-level 3
  Created user 8
  $ user3key=`mozreview create-api-key user3@example.com`

Dump the user so it gets mirrored over to Review Board

  $ rbmanage dump-user user3 > /dev/null

The user should not have an ldap username associated with them

  $ rbmanage dump-user-ldap user3
  no ldap username associated with user3

Calling the mozreview-ldap-associate pash command will prompt for username

  $ alias user3ssh="ssh -F ${MOZREVIEW_HOME}/ssh_config -i ${MOZREVIEW_HOME}/keys/user3@example.com -l user3@example.com -p ${HGSSH_PORT} ${HGSSH_HOST}"
  $ user3ssh mozreview-ldap-associate << EOF
  > EOF
  The following LDAP account will be associated with MozReview:
  
    user3@example.com
  
  By SSHing into this machine, you have proved ownership of that
  LDAP account. We will need Bugzilla credentials to prove ownership
  of a Bugzilla account. These credentials are NOT stored on the
  server.
  
  Enter your Bugzilla e-mail address:
  No username; aborting
  [1]

Entering a username will prompt for API Key

  $ user3ssh mozreview-ldap-associate << EOF
  > user3
  > EOF
  The following LDAP account will be associated with MozReview:
  
    user3@example.com
  
  By SSHing into this machine, you have proved ownership of that
  LDAP account. We will need Bugzilla credentials to prove ownership
  of a Bugzilla account. These credentials are NOT stored on the
  server.
  
  Enter your Bugzilla e-mail address:
  Enter a Bugzilla API Key:
  No API Key; aborting
  [1]

Username as command argument skips straight to API Key prompt

  $ user3ssh mozreview-ldap-associate user3 << EOF
  > EOF
  The following LDAP account will be associated with MozReview:
  
    user3@example.com
  
  By SSHing into this machine, you have proved ownership of that
  LDAP account. We will need Bugzilla credentials to prove ownership
  of a Bugzilla account. These credentials are NOT stored on the
  server.
  
  Bugzilla e-mail address: user3
  Enter a Bugzilla API Key:
  No API Key; aborting
  [1]

Specifying an invalid username results in error at association time

  $ user3ssh mozreview-ldap-associate << EOF
  > baduser@example.com
  > ${user3key}
  > EOF
  The following LDAP account will be associated with MozReview:
  
    user3@example.com
  
  By SSHing into this machine, you have proved ownership of that
  LDAP account. We will need Bugzilla credentials to prove ownership
  of a Bugzilla account. These credentials are NOT stored on the
  server.
  
  Enter your Bugzilla e-mail address:
  Enter a Bugzilla API Key:
  associating LDAP account user3@example.com with Bugzilla account baduser@example.com...
  error occurred!
  Verify you can log into MozReview at http://$DOCKER_HOSTNAME:$HGPORT1/
  Verify the Bugzilla API Key specified is valid.
  Seek help in #mozreview if this error persists
  [1]

Specifying an invalid API Key results in error

  $ user3ssh mozreview-ldap-associate << EOF
  > user3@example.com
  > badapikey
  > EOF
  The following LDAP account will be associated with MozReview:
  
    user3@example.com
  
  By SSHing into this machine, you have proved ownership of that
  LDAP account. We will need Bugzilla credentials to prove ownership
  of a Bugzilla account. These credentials are NOT stored on the
  server.
  
  Enter your Bugzilla e-mail address:
  Enter a Bugzilla API Key:
  associating LDAP account user3@example.com with Bugzilla account user3@example.com...
  error occurred!
  Verify you can log into MozReview at http://$DOCKER_HOSTNAME:$HGPORT1/
  Verify the Bugzilla API Key specified is valid.
  Seek help in #mozreview if this error persists
  [1]

Specifying a valid username and API Key will associate LDAP account

  $ user3ssh mozreview-ldap-associate << EOF
  > user3@example.com
  > ${user3key}
  > EOF
  The following LDAP account will be associated with MozReview:
  
    user3@example.com
  
  By SSHing into this machine, you have proved ownership of that
  LDAP account. We will need Bugzilla credentials to prove ownership
  of a Bugzilla account. These credentials are NOT stored on the
  server.
  
  Enter your Bugzilla e-mail address:
  Enter a Bugzilla API Key:
  associating LDAP account user3@example.com with Bugzilla account user3@example.com...
  LDAP account successfully associated!
  exiting

  $ rbmanage dump-user-ldap user3
  ldap username: user3@example.com

Create another user

  $ mozreview create-user user4@example.com user4password 'User Four [:user4]' --uid 2003 --scm-level 1
  Created user 9

Dump the user so it gets mirrored over to Review Board

  $ rbmanage dump-user user4 > /dev/null

The user should not have an ldap username associated with them

  $ rbmanage dump-user-ldap user4
  no ldap username associated with user4

Trigger automatic association

  $ rbmanage associate-employee-ldap --email user4@example.com
  user4@example.com associated with user4@example.com

The user should now have an associated ldap_username with appropriate logs

  $ rbmanage dump-user-ldap user4
  ldap username: user4@example.com
  $ mozreview exec rbweb grep -i ldap /reviewboard/logs/reviewboard.log | tail -n 1
  ????-??-?? ??:??:??,??? - INFO -  - root - Associating user: user4@example.com with ldap_username: user4@example.com (glob)

Create another user, where their username is different from their Bugzilla address

  $ mozreview create-user user5@example.com user5password 'User Five [:user5]' --uid 2004 --scm-level 1
  Created user 10
  $ rbmanage dump-user user5 > /dev/null
  $ mozreview delete-ldap-user user5@example.com
  $ mozreview create-ldap-user me@example.org user5 2004 'User Five [:user5]' --scm-level 1 --bugzilla-email=user5@example.com

Trigger automatic association

  $ rbmanage associate-employee-ldap --email user5@example.com
  user5@example.com associated with me@example.org
  $ mozreview exec rbweb grep -i ldap /reviewboard/logs/reviewboard.log | tail -n 1
  ????-??-?? ??:??:??,??? - INFO -  - root - Associating user: user5@example.com with ldap_username: me@example.org (glob)

Update Bugzilla address and reassociate

  $ mozreview delete-ldap-user me@example.org
  $ mozreview create-ldap-user you@example.org user5 2004 'User Five [:user5]' --scm-level 1 --bugzilla-email=user5@example.com
  $ rbmanage associate-employee-ldap --email user5@example.com
  user5@example.com associated with you@example.org
  $ mozreview exec rbweb grep -i ldap /reviewboard/logs/reviewboard.log | tail -n 1
  ????-??-?? ??:??:??,??? - INFO -  - root - Existing ldap association 'me@example.org' replaced by 'you@example.org' (glob)

Create two users with the same Bugzilla address

  $ mozreview create-user user6@example.com user6password 'User Six [:user6]' --uid 2005 --scm-level 1 --bugzilla-email conflict@example.com
  Created user 11
  $ mozreview create-user conflict@example.com conflictpassword 'Conflict [:conflict]' --uid 2006 --scm-level 1
  Created user 12

Dump the users so they are mirrored over to Review Board, then delete the
associations this created.

  $ rbmanage dump-user user6 > /dev/null
  $ rbmanage associate-ldap-user user6 none > /dev/null
  $ rbmanage dump-user conflict > /dev/null
  $ rbmanage associate-ldap-user conflict none > /dev/null

Trigger automatic association and check the logs

  $ rbmanage associate-employee-ldap --email conflict@example.com
  LDAP association failed.
  $ mozreview exec rbweb grep -i ldap /reviewboard/logs/reviewboard.log | tail -n 1
  ????-??-?? ??:??:??,??? - INFO -  - mozreview.ldap.resources - Could not update ldap association: More than one match for conflict@example.com (glob)

Ensure automatic association doesn't overwrite existing valid associations.

  $ mozreview create-user user7@example.com user7password 'User Seven [:user7]'
  Created user 13
  $ mozreview create-ldap-user uSeven@example.org uSeven 2007 'User Seven' --scm-level 1
  $ rbmanage dump-user user7 > /dev/null
  $ rbmanage associate-ldap-user user7 uSeven@example.org
  uSeven@example.org associated with user7
  $ rbmanage associate-employee-ldap --email user7@example.com
  user7@example.com already associated with uSeven@example.org
  $ mozreview exec rbweb grep -i ldap /reviewboard/logs/reviewboard.log | tail -n 1
  ????-??-?? ??:??:??,??? - INFO -  - root - Associating user: user7@example.com already associated with ldap_username: uSeven@example.org (glob)

Cleanup

  $ mozreview stop
  stopped 7 containers
