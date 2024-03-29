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

Treeherder link but no perfherder link if non-publishing phase and not autoland (e.g. Try)

  $ cd server
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo 
  > [web]
  > push_ssl = False
  > allow_push = *
  > [mozilla]
  > treeherder_repo = try
  > [phases]
  > publish = False
  > EOF
  $ hg serve -d -p $HGPORT2 --pid-file hg.pid --hgmo -E error-phases-try.log
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd ..
  $ http http://localhost:$HGPORT2/rev/be788785547b --body-file body > /dev/null
  $ grep '>treeherder' body
  <tr><td>treeherder</td><td>try@0a37bfb47d98 [<a href="https://treeherder.mozilla.org/jobs?repo=try&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e">default view</a>] [<a href="https://treeherder.mozilla.org/jobs?repo=try&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e&filter-resultStatus=testfailed&filter-resultStatus=busted&filter-resultStatus=exception">failures only]</td></tr>

  $ grep perfherder body
  [1]

Treeherder link and perfherder link if non-publishing phase and autoland

  $ cd server
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo 
  > [web]
  > push_ssl = False
  > allow_push = *
  > [mozilla]
  > treeherder_repo = autoland
  > [phases]
  > publish = False
  > EOF
  $ hg serve -d -p $HGPORT3 --pid-file hg.pid --hgmo -E error-phases-autoland.log
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd ..
  $ http http://localhost:$HGPORT3/rev/be788785547b --body-file body > /dev/null
  $ grep '>treeherder' body
  <tr><td>treeherder</td><td>autoland@0a37bfb47d98 [<a href="https://treeherder.mozilla.org/jobs?repo=autoland&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e">default view</a>] [<a href="https://treeherder.mozilla.org/jobs?repo=autoland&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e&filter-resultStatus=testfailed&filter-resultStatus=busted&filter-resultStatus=exception">failures only]</td></tr>

  $ grep perfherder body
  <tr><td>perfherder</td><td>[<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=autoland&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=autoland&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=1" target="_blank">talos</a>] [<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=autoland&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=autoland&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=2" target="_blank">build metrics</a>] [<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=autoland&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=autoland&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=6" target="_blank">platform microbench</a>] (compared to previous push)</td></tr>

Treeherder link and perfherder link if publishing phase

  $ cd server
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo 
  > [web]
  > push_ssl = False
  > allow_push = *
  > [mozilla]
  > treeherder_repo = mozilla-central
  > [phases]
  > publish = True
  > EOF
  $ hg serve -d -p $HGPORT4 --pid-file hg.pid --hgmo -E error-publishing.log
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd ..
  $ http http://localhost:$HGPORT4/rev/be788785547b --body-file body > /dev/null
  $ grep '>treeherder' body
  <tr><td>treeherder</td><td>mozilla-central@0a37bfb47d98 [<a href="https://treeherder.mozilla.org/jobs?repo=mozilla-central&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e">default view</a>] [<a href="https://treeherder.mozilla.org/jobs?repo=mozilla-central&revision=0a37bfb47d9849cceb609070a69c0715a176dd3e&filter-resultStatus=testfailed&filter-resultStatus=busted&filter-resultStatus=exception">failures only]</td></tr>

  $ grep perfherder body
  <tr><td>perfherder</td><td>[<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=mozilla-central&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=mozilla-central&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=1" target="_blank">talos</a>] [<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=mozilla-central&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=mozilla-central&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=2" target="_blank">build metrics</a>] [<a href="https://treeherder.mozilla.org/perf.html#/compare?originalProject=mozilla-central&originalRevision=0a37bfb47d9849cceb609070a69c0715a176dd3e&newProject=mozilla-central&newRevision=be788785547b64e986e9f219500f5f6d31de39b5&framework=6" target="_blank">platform microbench</a>] (compared to previous push)</td></tr>

Confirm no errors in logs

  $ cat server/error.log
  $ cat server/error-phases-autoland.log
  $ cat server/error-phases-try.log
  $ cat server/error-publishing.log
