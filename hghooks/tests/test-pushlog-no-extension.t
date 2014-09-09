  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.pushlog = python:mozhghooks.pushlog.log
  > EOF

  $ hg init client
  $ cd client
  $ touch foo
  $ hg commit -A -m 'initial'
  adding foo
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  repository not properly configured; missing pushlog extension.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.pushlog hook failed
  [255]
