  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.try_mandatory = python:mozhghooks.try_warning.hook
  > EOF

  $ hg init client
  $ cd client

Pushing a changeset without using try syntax should print a warning

  $ touch foo
  $ hg commit -A -m 'Bug 123 - Add foo'
  adding foo
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  **************************** WARNING ****************************
  Your push does not specify any jobs to run on try. You can still
  schedule jobs by selecting the drop down at the top right of your
  push in treeherder and choosing 'Add new Jobs'.
  
  For more information, see https://wiki.mozilla.org/Try.
  *****************************************************************
  

Pushing a changeset with '-p none' should error out

  $ echo 'working' > foo
  $ hg commit -m 'try: -b do -p none'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  ***************************** ERROR ******************************
  Your try syntax would not trigger any jobs. Either specify a build
  with '-p' or an arbitrary job with '-j'. If you intended to push
  without triggering any jobs, omit the try syntax completely.
  
  For more information, see https://wiki.mozilla.org/Try.
  ******************************************************************
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.try_mandatory hook failed
  [255]
 
Pushing a changeset with try syntax on the tip should be allowed

  $ hg commit --amend -m 'try: -b do -p all'
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/0eb01296232e-7764c983-amend*.hg (glob)
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
