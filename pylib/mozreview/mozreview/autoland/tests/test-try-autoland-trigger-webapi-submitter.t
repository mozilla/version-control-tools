Disabled because test is failing
#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Create the test users

  $ adminbugzilla create-user author@example.com password 'Patch Author'
  created user 6
  $ adminbugzilla create-user dummy1@example.com password 'Dummy User'
  created user 7

Create and publish a review request

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com push http://localhost:$HGPORT/test-repo > /dev/null
  $ rbmanage publish $HGPORT1 1

Try to trigger the WebAPI endpoint as user@dummy, which should fail, because
dummy1@example.com is not the submitter.

  $ exportbzauth dummy1@example.com password

Force the dummy Review Board user to be created by querying for it.

  $ rbmanage get-users $HGPORT1 ''
  - id: 1
    url: /users/author%2B6/
    username: author+6
  - id: 2
    url: /users/dummy1%2B7/
    username: dummy1+7

  $ rbmanage hit-try-autoland-trigger $HGPORT1 1 "try -b do -p all -t none -u all"
  You don't have permission for this (HTTP 403, API Error 101)
  [1]

Try to trigger the WebAPI endpoint as the submitter, which should succeed.

  $ exportbzauth author@example.com password
  $ rbmanage hit-try-autoland-trigger $HGPORT1 1 "try -b do -p all -t none -u all" --autoland-request-id=1

That should have succeeded in adding a row to the AutolandRequests table with
the request id 1.

Force the admin Review Board user to be created by querying for it.

  $ rbmanage get-users $HGPORT1 ''
  - id: 1
    url: /users/author%2B6/
    username: author+6
  - id: 2
    url: /users/dummy1%2B7/
    username: dummy1+7

  $ rbmanage dump-autoland-requests $HGPORT1
  autoland_id: 1
  last_known_status: R
  push_revision: 57755461e85f1e3e66738ec2d57f325249897409
  repository_revision: ''
  repository_url: ''
  review_request_id: 1
  user_id: 1


  $ cd ..
  $ mozreview stop
  stopped 6 containers
