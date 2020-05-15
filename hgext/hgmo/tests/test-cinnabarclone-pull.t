  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > cinnabarclone = /app/venv/git-cinnabar/mercurial/cinnabarclone.py
  > EOF

  $ startserver

  $ cd server
  $ touch foo
  $ hg -q commit -A -m initial
  $ cd ..

  $ hg -q clone http://localhost:$HGPORT repo
  $ cd repo

cinnabar.manifest should not be transferred by default

  $ hg pull
  pulling from http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found
  $ ls .hg
  00changelog.i
  branch
  cache
  dirstate
  hgrc
  requires
  store
  undo.bookmarks
  undo.branch
  undo.desc
  undo.dirstate
  wcache (hg49 !)


Even if enabled and the server doesn't have a cinnabar.manifest

  $ hg --config hgmo.pullclonebundlesmanifest=true pull
  pulling from http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found
  $ ls .hg
  00changelog.i
  branch
  cache
  dirstate
  hgrc
  requires
  store
  undo.bookmarks
  undo.branch
  undo.desc
  undo.dirstate
  wcache (hg49 !)


Sanity check that clone bundles manifest is served properly

  $ cat > ../server/.hg/cinnabar.manifest << EOF
  > https://www.example.com
  > EOF

  $ http --no-headers http://localhost:$HGPORT/?cmd=cinnabarclone
  200
  
  https://www.example.com
  

cinnabar.manifest should not be transferred by default

  $ hg pull
  pulling from http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found

  $ cat .hg/cinnabar.manifest
  cat: .hg/cinnabar.manifest: No such file or directory
  [1]
  $ ls .hg
  00changelog.i
  branch
  cache
  dirstate
  hgrc
  requires
  store
  undo.bookmarks
  undo.branch
  undo.desc
  undo.dirstate
  wcache (hg49 !)

enabling config option pulls the manifest

  $ hg --config hgmo.pullclonebundlesmanifest=true pull
  pulling from http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found
  pulling cinnabarclone manifest

  $ cat .hg/cinnabar.manifest
  https://www.example.com

A missing manifest results in the local file being deleted

  $ rm -f ../server/.hg/cinnabar.manifest
  $ hg --config hgmo.pullclonebundlesmanifest=true pull
  pulling from http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found
  deleting local cinnabar.manifest

  $ ls .hg
  00changelog.i
  branch
  cache
  dirstate
  hgrc
  requires
  store
  undo.bookmarks
  undo.branch
  undo.desc
  undo.dirstate
  wcache (hg49 !)


Confirm no errors in log

  $ cat ../server/error.log
