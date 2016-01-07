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

  $ hg --config bugzilla.username=user1@example.com --config bugzilla.apikey=${user1key} push -r 1 --reviewid 1
  pushing to ssh://*:$HGPORT6/test-repo (glob)
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/cd3395bd3f8a*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:60479d07173e
  summary:    second commit
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/mynick
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
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

Cleanup

  $ mozreview stop
  stopped 10 containers
