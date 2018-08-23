  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > unifyrepo = $TESTDIR/hgext/unifyrepo/__init__.py
  > pushlog = $TESTDIR/hgext/pushlog/
  > EOF

  $ cat > unifyconfig << EOF
  > [GLOBAL]
  > stagepath = $TESTTMP/servers/stagerepo
  > destpath = $TESTTMP/servers/destrepo
  > [unifyrepo1]
  > path = $TESTTMP/servers/unifyrepo1
  > pullrevs = 0::tip^
  > [unifyrepo2]
  > bookmark = repo2
  > path = $TESTTMP/servers/unifyrepo2
  > [unifyrepo3]
  > nobookmark = true
  > path = $TESTTMP/servers/unifyrepo3
  > EOF

Create an origin repo and make copies

  $ mkdir servers
  $ mkdir clients
  $ hg init servers/originrepo
  $ hg init clients/originrepo
  $ cd clients/originrepo
  $ echo foo > foo
  $ hg -q addremove
  $ hg -q commit -A -m "SOURCE COMMIT"
  $ hg -q push ../../servers/originrepo
  recorded push in pushlog
  $ cd ../../servers
  $ cp -r originrepo stagerepo
  $ cp -r originrepo destrepo
  $ cp -r originrepo unifyrepo1
  $ cp -r originrepo unifyrepo2
  $ cp -r originrepo unifyrepo3

Create a repo with a different origin

  $ cd ..
  $ hg init servers/differentrepo
  $ hg init clients/differentrepo

Serve the repos so we get pushlog information

  $ cat > hgweb.conf << EOF
  > [paths]
  > /unifyrepo1 = $TESTTMP/servers/unifyrepo1
  > /unifyrepo2 = $TESTTMP/servers/unifyrepo2
  > /unifyrepo3 = $TESTTMP/servers/unifyrepo3
  > /differentrepo = $TESTTMP/servers/differentrepo
  > [web]
  > refreshinterval = -1
  > EOF
  $ hg --config extensions.pushlog=$TESTDIR/hgext/pushlog serve -d -p $HGPORT --pid-file hg.pid --web-conf hgweb.conf -E error_log.log
  $ cat hg.pid >> $DAEMON_PIDS


Set up repo 1 to test `pullrevs` config option

  $ cd clients
  $ hg -q clone ../servers/unifyrepo1 unifyrepo1
  $ cd unifyrepo1
  $ echo bar > foo
  $ hg -q commit -A -m "repo1 commit1"
  $ echo foobar > foo
  $ hg -q commit -A -m "repo1 commit2"
  $ hg -q push ../../servers/unifyrepo1
  recorded push in pushlog
  $ echo excluded > foo
  $ hg -q commit -A -m "repo1 commit3 EXCLUDED"
  $ hg -q push ../../servers/unifyrepo1
  recorded push in pushlog

  $ hg log -G -T '{desc}\n'
  @  repo1 commit3 EXCLUDED
  |
  o  repo1 commit2
  |
  o  repo1 commit1
  |
  o  SOURCE COMMIT
  
  $ hg -R ../../servers/unifyrepo1 log -G -T '{desc}\n'
  o  repo1 commit3 EXCLUDED
  |
  o  repo1 commit2
  |
  o  repo1 commit1
  |
  o  SOURCE COMMIT
  

Set up repo 2 to test `bookmark` config section.
We expect to see a bookmark named "repo2" in the
unified repository

  $ cd ..
  $ hg -q clone ../servers/unifyrepo2 unifyrepo2
  $ cd unifyrepo2
  $ echo bar > bar
  $ hg -q addremove
  $ hg -q commit -A -m "repo2 commit0"
  $ echo barbar > bar
  $ hg -q commit -A -m "repo2 commit1"
  $ echo barbarbar > bar
  $ hg -q commit -A -m "repo2 commit2 BOOKMARK"
  $ hg -q push ../../servers/unifyrepo2
  recorded push in pushlog

  $ hg log -G -T '{desc}\n'
  @  repo2 commit2 BOOKMARK
  |
  o  repo2 commit1
  |
  o  repo2 commit0
  |
  o  SOURCE COMMIT
  
  $ hg -R ../../servers/unifyrepo2 log -G -T '{desc}\n'
  o  repo2 commit2 BOOKMARK
  |
  o  repo2 commit1
  |
  o  repo2 commit0
  |
  o  SOURCE COMMIT
  

Set up repo3, there should be no bookmark for this repo 

  $ cd ..
  $ hg -q clone ../servers/unifyrepo3 unifyrepo3
  $ cd unifyrepo3
  $ echo barz > barz
  $ hg -q addremove
  $ hg -q commit -A -m "repo3 commit0"
  $ hg -q push ../../servers/unifyrepo3
  recorded push in pushlog
  $ echo barbarz > barz
  $ hg -q commit -A -m "repo3 commit1"
  $ hg -q push ../../servers/unifyrepo3
  recorded push in pushlog
  $ echo barbarbarz > barz
  $ hg -q commit -A -m "repo3 commit2 NOBOOKMARK"
  $ hg -q push ../../servers/unifyrepo3
  recorded push in pushlog

  $ hg log -G -T '{desc}\n'
  @  repo3 commit2 NOBOOKMARK
  |
  o  repo3 commit1
  |
  o  repo3 commit0
  |
  o  SOURCE COMMIT
  
  $ hg -R ../../servers/unifyrepo3 log -G -T '{desc}\n'
  o  repo3 commit2 NOBOOKMARK
  |
  o  repo3 commit1
  |
  o  repo3 commit0
  |
  o  SOURCE COMMIT
  

`hg unifyrepo` fails without pushlog

  $ cd ..
  $ hg unifyrepo ../unifyconfig --config extensions.pushlog=!
  abort: pushlog API not available
  (is the pushlog extension loaded?)
  [255]

Perform unification and examine graph structure. We should see:
+   - No bookmark on the commit with NOBOOKMARK in the commit message,
+     as nobookmark is set to true
+   - Bookmark "repo2" on the tip of the unifyrepo2 dag branch, due to the
+     bookmark option being specified
+   - Bookmark "unifyrepo1" on the tip of the unifyrepo1 dag branch,
+     due to nobookmark and bookmark both being omitted and therefore
+     the bookmark name is seeded from the repo name
+   - No commit with "EXCLUDED" in the commit message
+   - Common origin commit for the repo

  $ hg unifyrepo ../unifyconfig --skipreplicate
  pulling $TESTTMP/servers/unifyrepo1 into $TESTTMP/servers/stagerepo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  new changesets 082ed5a15c23:849054522f6d
  pulling $TESTTMP/servers/unifyrepo2 into $TESTTMP/servers/stagerepo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets c82636ead3ee:b0dd06b54e65
  pulling $TESTTMP/servers/unifyrepo3 into $TESTTMP/servers/stagerepo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets fef1d0f689fc:bd139f07f0da
  obtained pushlog info for 4/4 revisions from 3 pushes from unifyrepo1
  obtained pushlog info for 4/4 revisions from 2 pushes from unifyrepo2
  obtained pushlog info for 4/4 revisions from 4 pushes from unifyrepo3
  aggregating 3/4 revisions for 0 heads from unifyrepo1
  aggregating 4/4 revisions for 1 heads from unifyrepo2
  aggregating 4/4 revisions for 1 heads from unifyrepo3
  aggregating 9/10 nodes from 9 original pushes
  8/9 nodes will be pulled
  consolidated into 3 pulls from 6 unique pushes
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  new changesets 082ed5a15c23:1a65f2b9519d
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets c82636ead3ee:b0dd06b54e65
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files (+1 heads)
  new changesets fef1d0f689fc:bd139f07f0da
  inserting 5 pushlog entries
  writing 2 bookmarks

  $ cd ../servers/destrepo
  $ hg log -G -T '{desc}\n'
  o  repo3 commit2 NOBOOKMARK
  |
  o  repo3 commit1
  |
  o  repo3 commit0
  |
  | o  repo2 commit2 BOOKMARK
  | |
  | o  repo2 commit1
  | |
  | o  repo2 commit0
  |/
  | o  repo1 commit2
  | |
  | o  repo1 commit1
  |/
  o  SOURCE COMMIT
  

Unification of repos with different origin changeset unsupported

  $ cd ../../clients/differentrepo
  $ echo test > test
  $ hg -q addremove
  $ hg -q commit -A -m "non-shared origin"
  $ echo testtest > test
  $ hg -q addremove
  $ hg -q commit -A -m "nonshared commit2"
  $ hg -q push ../../servers/differentrepo
  recorded push in pushlog

Add a section for a repo with a different origin commit, this should fail
as it is an unsupported use case.

  $ cd ../..
  $ cat >> unifyconfig << EOF
  > [differentrepo]
  > path = $TESTTMP/servers/differentrepo
  > EOF
  $ hg unifyrepo unifyconfig
  abort: repository has different rev 0: unifyrepo1
  
  [255]

Confirm no output in logs

  $ cat error_log.log
