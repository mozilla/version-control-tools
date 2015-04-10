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
  $ mozreview create-ldap-user author@example.com author 2001 'Patch Author' --key-file ${MOZREVIEW_HOME}/keys/author@example.com --scm-level 1

Create and publish a review request

  $ exportbzauth author@example.com password
  $ bugzilla create-bug TestProduct TestComponent 'First Bug'
  $ echo initial > foo
  $ hg commit -m 'Bug 1 - Initial commit to review'
  $ hg --config bugzilla.username=author@example.com push > /dev/null
  $ rbmanage publish 1

Try to trigger the WebAPI endpoint as the submitter, which should succeed.

  $ exportbzauth author@example.com password
  $ rbmanage hit-try-autoland-trigger 1 "try -b do -p all -t none -u all" --autoland-request-id=1

That should have succeeded in adding a row to the AutolandRequests table with
the request id 1.

Force the admin Review Board user to be created by querying for it.

  $ rbmanage get-users ''
  - id: 1
    url: /users/admin%2B1/
    username: admin+1
  - id: 2
    url: /users/author%2B6/
    username: author+6

  $ rbmanage dump-autoland-requests
  autoland_id: 1
  last_known_status: R
  push_revision: 57755461e85f1e3e66738ec2d57f325249897409
  repository_revision: ''
  repository_url: ''
  review_request_id: 1
  user_id: 2

Hit the WebAPI with the Autoland response

  $ rbmanage hit-autoland-request-update 1 mozilla-central abcdefghijklmnop try "try -b do -p all -t none -u all" true Foo
  $ rbmanage dump-autoland-requests
  autoland_id: 1
  last_known_status: S
  push_revision: 57755461e85f1e3e66738ec2d57f325249897409
  repository_revision: Foo
  repository_url: ''
  review_request_id: 1
  user_id: 2

  $ cd ..
  $ mozreview stop
  stopped 8 containers
