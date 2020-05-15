  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
  > 
  > [extensions]
  > mozext = $TESTDIR/hgext/mozext
  > localmozrepo = $TESTDIR/testing/local-mozilla-repos.py
  > 
  > [localmozrepo]
  > readuri = http://localhost:$HGPORT/
  > writeuri = ssh://user@dummy/$TESTTMP/
  > EOF

  $ export PUSHLOGHG=/app/venv/mercurials/5.3.2/bin/hg

  $ export USER=hguser
  $ hg init mozilla-central
  $ cd mozilla-central
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog/__init__.py
  > pushlog-feed = $TESTDIR/hgext/pushlog/feed.py
  > hgmo = $TESTDIR/hgext/hgmo
  > EOF
  $ cd ..
  $ cat > hgweb.conf << EOF
  > [paths]
  > / = $TESTTMP/*
  > [web]
  > push_ssl = False
  > allow_push = *
  > EOF
  $ $PUSHLOGHG serve -d -p $HGPORT --pid-file server.pid --web-conf hgweb.conf -E error.log
  $ cat server.pid >> $DAEMON_PIDS

Set up a repository

  $ hg init client
  $ cd client
  $ touch baz
  $ hg -q commit -A -m "initial DONTBUILD"
  $ mkdir config
  $ cat > config/milestone.txt << EOF
  > # Some comments
  > 14.0
  > EOF
  $ hg commit -A -m 'No bug: Milestone added'
  adding config/milestone.txt
  $ touch bar
  $ hg commit -A -m 'Bar'
  adding bar
  $ hg backout -r tip
  removing bar
  changeset 3:ac2b8cb4ecf5 backs out changeset 2:98175e4fd343
  $ echo foo > bar
  $ hg commit -A -m 'Bug 1234567,9101112: print a commit on the command line r?glob,smacleod,hguser'
  adding bar
  $ hg bookmark -r tip central
  $ hg push http://localhost:$HGPORT/mozilla-central -B central
  pushing to http://$LOCALHOST:$HGPORT/mozilla-central
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 5 changesets with 4 changes to 3 files
  remote: recorded push in pushlog
  exporting bookmark central
  $ cd ..

Pull via http:// will fetch pushlog

  $ hg clone -U http://localhost:$HGPORT/mozilla-central clonehttp
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 4 changes to 3 files
  added 1 pushes
  new changesets 28d014a3f251:d6d34e5ea05c

Pull via ssh:// will not fetch pushlog
Fails on Mercurials pre-4.8 due to Pushlog extension incompatible versions.
Our hack to load pushlog with a compatible version only works for `hg serve`
processes using HTTP

#if hg48
  $ hg clone -U ssh://user@dummy/$TESTTMP/mozilla-central clonessh
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 4 changes to 3 files
  cannot fetch pushlog when pulling via ssh://; you should be pulling via https://
  new changesets 28d014a3f251:d6d34e5ea05c
#endif

Show the dag

  $ cd clonehttp

  $ hg log -G
  o  changeset:   4:d6d34e5ea05c
  |  bookmark:    central
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Bug 1234567,9101112: print a commit on the command line r?glob,smacleod,hguser
  |
  o  changeset:   3:ac2b8cb4ecf5
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Backed out changeset 98175e4fd343
  |
  o  changeset:   2:98175e4fd343
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Bar
  |
  o  changeset:   1:a16e73662286
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     No bug: Milestone added
  |
  o  changeset:   0:28d014a3f251
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     initial DONTBUILD
  

  $ cat >> .hg/hgrc << EOF
  > [ui]
  > username = hguser
  > [extensions]
  > mozext = $TESTDIR/hgext/mozext
  > [mozext]
  > ircnick = hguser
  > EOF

`me()` should match several values

  $ hg log -r'me()' -T '{node}\n'  
  d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

  $ hg --config ui.username= log -r'me()' -T '{node}\n'
  abort: "[ui] username" must be set to use me()
  [255]

`dontbuild()` should match the commit that includes the magic words

  $ hg log -r'dontbuild()' -T '{node}\n'
  28d014a3f25108f2394610a033bf0bc8444c4f2f

`bug(N)` returns changesets for the given bug

  $ hg log -r'bug(1234567)' -T '{node}\n'
  d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

`nobug()` returns changesets tagged as having no bug

  $ hg log -r'nobug()' -T '{node}\n'
  28d014a3f25108f2394610a033bf0bc8444c4f2f
  a16e73662286ca2da14258dc8896eaafcf481c8e
  98175e4fd343bc8e1e36d62982c9d5504c7f6419
  ac2b8cb4ecf54cae779009fe21f5fab7fce71ce4

`pushhead()` gets all heads for all trees, or a given tree

  $ hg log -r'pushhead()' -T '{node}\n'
  d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

  $ hg log -r'pushhead(central)' -T '{node}\n'
  d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

`reviewer(name)` gets changes reviewed by "name"

  $ hg log -r'reviewer(glob)' -T '{node}\n'
  d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

`reviewed()` gets reviewed changesets

  $ hg log -r'reviewed()' -T '{node}\n'
  d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

`firstpushtree(central)` gets changes first pushed to the specified tree

  $ hg log -r'firstpushtree(central)' -T '{node}\n'
  28d014a3f25108f2394610a033bf0bc8444c4f2f
  a16e73662286ca2da14258dc8896eaafcf481c8e
  98175e4fd343bc8e1e36d62982c9d5504c7f6419
  ac2b8cb4ecf54cae779009fe21f5fab7fce71ce4
  d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

`firstpushdate()` should return no revisions for very recent date and all for very old date

  $ hg log -r'firstpushdate("> now")'
  $ hg log -r'firstpushdate("-1")' -T'{desc|firstline}\n'
  initial DONTBUILD
  No bug: Milestone added
  Bar
  Backed out changeset 98175e4fd343
  Bug 1234567,9101112: print a commit on the command line r?glob,smacleod,hguser

`pushdate()` returns the same as above
{firstpushdate} yields a date that can be parsed by a template filter


  $ hg log -r'pushdate("> now")'
  $ hg log -r'pushdate("-1")' -T'{rev} {firstpushdate|shortdate}\n'
  0 [0-9]{4}-[0-9]{2}-[0-9]{2} (re)
  1 [0-9]{4}-[0-9]{2}-[0-9]{2} (re)
  2 [0-9]{4}-[0-9]{2}-[0-9]{2} (re)
  3 [0-9]{4}-[0-9]{2}-[0-9]{2} (re)
  4 [0-9]{4}-[0-9]{2}-[0-9]{2} (re)

{backedoutby} template works

  $ hg log -r 98175e4fd343 --template '{backedoutby}\n'
  ac2b8cb4ecf54cae779009fe21f5fab7fce71ce4

{backsoutnodes} template works

  $ hg log -r ac2b8cb4ecf5 --template '{join(backsoutnodes, " ")}\n'
  98175e4fd343

{bug} template returns first bug in commit message

  $ hg log -r 4 --template '{bug}\n'
  1234567

{bugs} template returns all bugs in commit message

  $ hg log -r 4 --template '{join(bugs, " ")}\n'
  1234567 9101112

{reviewer} template returns first reviewer in commit message

  $ hg log -r 4 --template '{reviewer}\n'
  glob

{reviewers} template returns all reviewers in commit message

  $ hg log -r 4 --template '{join(reviewers, " ")}\n'
  glob smacleod hguser

{firstrelease} template works

  $ hg log -r 4 --template '{firstrelease}\n'
  
{firstbeta} template works

  $ hg log -r 4 --template '{firstbeta}\n'
  
{firstnightly} template works

  $ hg log -r 4 --template '{firstnightly}\n'
  14.0

{nightlydate} template works

  $ hg log -r 4 --template '{nightlydate}\n'
  [0-9]{4}-[0-9]{2}-[0-9]{2} (re)

{firstpushuser} template works

  $ hg log -r 4 --template '{firstpushuser}\n'
  hguser

{firstpushtree} template works

  $ hg log -r 4 --template '{firstpushtree}\n'
  central

{firstpushtreeherder} template works

  $ hg log -r 4 --template '{firstpushtreeherder}\n'
  https://treeherder.mozilla.org/#/jobs?repo=mozilla-central&revision=d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

{pushdates} template works

  $ hg log -r 4 --template '{pushdates % "{date|shortdate}"}\n'
  1970-01-01

{pushheaddates} template works

  $ hg log -r 4 --template '{pushheaddates % "{date|shortdate}"}\n'
  1970-01-01

{trees} template works

  $ hg log -r 4 --template '{trees}\n'
  central

{reltrees} template works

  $ hg log -r 4 --template '{reltrees}\n'
  central

Confirm no errors in log

  $ cat ../error.log


TODOS
=====

- functionality that calls out to `mozautomation` for tree uris and other information
- functionality that uses the local database (ie not the pushlog)

`tree(tree)` gets changes in the specified tree
This could probably be removed in favor of `::central` and `firefoxtree`

$ hg log -r'tree(central)' -T '{node}\n'
28d014a3f25108f2394610a033bf0bc8444c4f2f
a16e73662286ca2da14258dc8896eaafcf481c8e
98175e4fd343bc8e1e36d62982c9d5504c7f6419
ac2b8cb4ecf54cae779009fe21f5fab7fce71ce4
d6d34e5ea05c48d5ae40f6f3d73beae8babe509c

`hg treestatus` show status of some trees
convert this to a mach command instead?

`hg treeherder` opens treeherder view for given revision
on specified tree. Again, probably better as a mach command
where we can support Git as well

`hg changesetpushes` shows pushlog entries for a changeset
Doesn't work for me

`hg buginfo` shows information about patches with a given bug
This can be achieved using the `bug()` revset predicate,
might be worth removing
