  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.try_mandatory = python:mozhghooks.try_mandatory.hook
  > EOF

  $ hg init client
  $ cd client

Pushing a changeset without using try syntax should error

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
  
  
  ************************** ERROR ****************************
  To push to try you must use try syntax in the push comment of the * (glob)
  See http://trychooser.pub.build.mozilla.org/ to build your syntax
  For assistance using the syntax, see https://wiki.mozilla.org/Build:TryChooser.
  Thank you for helping to reduce CPU cyles by asking for exactly what you need.
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.try_mandatory hook failed
  [255]

Pushing a changeset with try syntax on the tip should be allowed

  $ echo 'working' > foo
  $ hg commit -m 'try: -b do -p all'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  Looks like you used try syntax, going ahead with the push.
  If you don't get what you expected, check http://trychooser.pub.build.mozilla.org/
  for help with building your trychooser request.
  Thanks for helping save resources, you're the best!
