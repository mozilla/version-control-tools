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

  $ rbmanage ../rbserver stop
  $ $TESTDIR/testing/docker-control.py stop-bmo rb-test-auth > /dev/null
