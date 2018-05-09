  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [hooks]
  > prepushkey.prevent_bookmarks = python:mozhghooks.prevent_bookmarks.hook
  > EOF
  $ cd ..

  $ hg clone server client
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Pushing a bookmark is not allowed

  $ hg book book1
  $ hg push -B book1
  pushing to $TESTTMP/server
  searching for changes
  no changes found
  bookmarks are disabled on this repository; refusing to accept modification to "book1"
  pushkey-abort: prepushkey.prevent_bookmarks hook failed (no-hg45 !)
  abort: exporting bookmark book1 failed! (no-hg45 !)
  abort: prepushkey.prevent_bookmarks hook failed (hg45 !)
  [255]

Pulling a bookmark on the server is allowed

  $ cd ../server
  $ hg pull ../client
  pulling from ../client
  searching for changes
  no changes found
  adding remote bookmark book1
