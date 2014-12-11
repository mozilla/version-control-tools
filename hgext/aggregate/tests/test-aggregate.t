  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
  $ populatedummydata root >/dev/null

  $ hg init client
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > aggregate = $TESTDIR/hgext/aggregate
  > 
  > [paths]
  > central = http://localhost:$HGPORT/mozilla-central
  > inbound = http://localhost:$HGPORT/integration/mozilla-inbound
  > EOF

Initial aggregation should pull from multiple remotes

  $ hg aggregate
  pulling from http://localhost:$HGPORT/mozilla-central
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  pulling from http://localhost:$HGPORT/integration/mozilla-inbound
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  aggregated 4 changesets from 2 repos

Subsequent aggregation should no-op

  $ hg aggregate
  no changesets aggregated

Install a new commit on central and aggregate

  $ cd ../root/mozilla-central
  $ echo new > foo
  $ hg commit -m 'new central'

  $ cd ../../client
  $ hg aggregate
  pulling from http://localhost:$HGPORT/mozilla-central
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  aggregated 1 changesets from 1 repos

Test repo-aggregate.py

  $ $TESTDIR/hgext/aggregate/repo-aggregate.py `which hg` . --maximum 3 --delay 1
  no changesets aggregated
  no changesets aggregated
  no changesets aggregated
