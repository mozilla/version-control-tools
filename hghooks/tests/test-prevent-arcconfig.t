  $ . $TESTDIR/hghooks/tests/common.sh

`conduit-testing` repos should only allow the dev/stage phab server in `.arcconfig`.

  $ hg init conduit-testing
  $ configurehooks conduit-testing
  $ hg -q clone conduit-testing client
  $ cd client
  $ echo '{"phabricator.uri":"https://phabricator-dev.allizom.org/"}' > .arcconfig
  $ hg ci -q -A -m "add .arcconfig"
  $ hg push
  pushing to $TESTTMP/conduit-testing
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ echo '{"phabricator.uri":"https://phabricator.allizom.org/"}' > .arcconfig
  $ hg ci -q -A -m "add .arcconfig"
  $ hg push
  pushing to $TESTTMP/conduit-testing
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ echo '{"phabricator.uri":"https://phabricator.services.mozilla.com/"}' > .arcconfig
  $ hg ci -q -A -m "update .arcconfig to bad value"
  $ hg push
  pushing to $TESTTMP/conduit-testing
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ******************************* ERROR ********************************
  Push contains unwanted changes to `.arcconfig` files.
  
  Please ensure `.arcconfig` points to the Phab dev or stage servers for
  `conduit-testing` repos.
  **********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]

Pushes that use the override flag should be allowed.

  $ hg ci -q --amend -m "update .arcconfig to bad value ARCCONFIG_OVERRIDE"
  $ hg push
  pushing to $TESTTMP/conduit-testing
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Pushes that update `.arcconfig` and then revert it should be allowed.

  $ echo '{"phabricator.uri":"https://phabricator-dev.allizom.org/"}' > .arcconfig
  $ hg ci -q -A -m "revert .arcconfig to correct value"
  $ echo '{"phabricator.uri":"https://phabricator.services.mozilla.com/"}' > .arcconfig
  $ hg ci -q -A -m "update .arcconfig to bad value"
  $ hg push
  pushing to $TESTTMP/conduit-testing
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  ******************************* ERROR ********************************
  Push contains unwanted changes to `.arcconfig` files.
  
  Please ensure `.arcconfig` points to the Phab dev or stage servers for
  `conduit-testing` repos.
  **********************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
  $ echo '{"phabricator.uri":"https://phabricator-dev.allizom.org/"}' > .arcconfig
  $ hg ci -q -A -m "revert .arcconfig to correct value"
  $ hg log -G
  @  changeset:   5:764d444c2720
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     revert .arcconfig to correct value
  |
  o  changeset:   4:48876a3cbb5d
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     update .arcconfig to bad value
  |
  o  changeset:   3:3f6c6789715e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     revert .arcconfig to correct value
  |
  o  changeset:   2:6050dfef4178
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     update .arcconfig to bad value ARCCONFIG_OVERRIDE
  |
  o  changeset:   1:4ed1c3bebe91
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     add .arcconfig
  |
  o  changeset:   0:58f2675adc14
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     add .arcconfig
  
  $ hg push
  pushing to $TESTTMP/conduit-testing
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files

  $ cd ..

