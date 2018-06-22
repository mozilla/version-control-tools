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
  $ grep perfherder body
  [1]

Configure the Treeherder repo

  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [mozilla]
  > treeherder_repo = mozilla-central
  > EOF

Confirm no errors in log

  $ cat error.log

Start a new server so the config is refreshed

  $ hg serve -d -p $HGPORT1 --pid-file hg.pid --hgmo -E error2.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Treeherder results link should be exposed
(Note the SHA-1 is different, as TreeHerder indexes by push head)

  $ http http://localhost:$HGPORT1/rev/be788785547b --body-file body > /dev/null
  $ grep '>treeherder' body
  <tr><td>treeherder</td><td>mozilla-central@0a37bfb47d98 [<a href="https://treeherder.mozilla.org/#/jobs?repo=mozilla-central&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e">default view</a>] [<a href="https://treeherder.mozilla.org/#/jobs?repo=mozilla-central&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e&filter-resultStatus=testfailed&filter-resultStatus=busted&filter-resultStatus=exception">failures only]</td></tr>

  $ grep perfherder body
  <tr><td>perfherder</td><td>[<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=mozilla-central&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=mozilla-central&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=1" target="_blank">talos</a>] [<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=mozilla-central&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=mozilla-central&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=2" target="_blank">build metrics</a>] [<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=mozilla-central&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=mozilla-central&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=6" target="_blank">platform microbench</a>] (compared to previous push)</td></tr>

Confirm no errors in log

  $ cat ./server/error2.log
