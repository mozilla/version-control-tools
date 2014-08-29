  $ hg init server
  $ cd server
  $ cat > .hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.changelog_correctness = python:mozhghooks.changelog_correctness.hook
  > EOF

  $ echo foo > foo
  $ echo bar > bar
  $ hg commit -A -m 'initial commit'
  adding bar
  adding foo

  $ cd ..
  $ hg clone server client
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client

Try a non-broken push

  $ echo baz > baz
  $ hg commit -A -m 'add baz'
  adding baz
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Create a broken changeset

  $ python $TESTDIR/hghooks/tests/changelog_correctness_helper.py

  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 0 files
  
  You apparently used `hg rebase` before pushing, and your mercurial
  version stores inconsistent metadata when doing so. Please upgrade
  mercurial or avoid `hg rebase`.
  Following is the list of changesets from your push with
  inconsistent metadata:
     46d74a44c0f9
  
  See http://wiki.mozilla.org/Troubleshooting_Mercurial#Fix_rebase
  for possible instructions how to fix your push.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.changelog_correctness hook failed
  [255]
