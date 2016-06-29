  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m initial

  $ hg -q push

  $ echo 1 > foo
  $ hg commit -m 1
  $ echo 2 > foo
  $ hg commit -m 2
  $ hg -q push

  $ cd ..

No Treeherder link unless the repository defines its Treeherder repo

  $ http http://localhost:$HGPORT/rev/be788785547b --body-file body > /dev/null
  $ grep '>treeherder' body
  [1]

Configure the Treeherder repo

  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [mozilla]
  > treeherder_repo = mozilla-central
  > EOF

Start a new server so the config is refreshed

  $ hg serve -d -p $HGPORT1 --pid-file hg.pid --hgmo
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Treeherder results link should be exposed
(Note the SHA-1 is different, as TreeHerder indexes by push head)

  $ http http://localhost:$HGPORT1/rev/be788785547b --body-file body > /dev/null
  $ grep '>treeherder' body
  <tr><td>treeherder</td><td>mozilla-central@0a37bfb47d98 [<a href="https://treeherder.mozilla.org/#/jobs?repo=mozilla-central&revision=0a37bfb47d98">default view</a>] [<a href="https://treeherder.mozilla.org/#/jobs?repo=mozilla-central&revision=0a37bfb47d98&filter-resultStatus=testfailed&filter-resultStatus=busted&filter-resultStatus=exception">failures only]</td></tr>
