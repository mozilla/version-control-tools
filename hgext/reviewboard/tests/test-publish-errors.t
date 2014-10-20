#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh

  $ commonenv rb-test-publish-errrs

  $ cd client
  $ echo foo > foo
  $ hg commit -A -m 'root commit'
  adding foo
  $ hg phase --public -r .

Referencing a bug that doesn't exist should throw a graceful error during publish

  $ echo nobug > foo
  $ hg commit -m 'Bug 1 - Does not exist'
  $ hg push http://localhost:$HGPORT
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:e2dc0a36abb9
  summary:    Bug 1 - Does not exist
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://1/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

  $ rbmanage publish $HGPORT1 1
  API Error: 500: 225: Invalid bug ID "1".
  [1]

TODO test publishing against a confidential bug (waiting on BMO API)

  $ cd ..

Cleanup

  $ rbmanage rbserver stop
  $ $TESTDIR/testing/docker-control.py stop-bmo rb-test-autocomplete > /dev/null
