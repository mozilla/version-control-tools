  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > EOF

  $ startserver

  $ cd server
  $ touch foo
  $ hg -q commit -A -m initial
  $ cd ..

  $ hg -q clone http://localhost:$HGPORT repo
  $ cd repo

clonebundles.manifest should not be transferred by default

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


Even if enabled and the server doesn't have a clonebundles.manifest

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

  $ cat > ../server/.hg/clonebundles.manifest << EOF
  > https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  > https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  > EOF

  $ http --no-headers http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  

clonebundles.manifest should not be transferred by default

  $ hg pull
  pulling from http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found

  $ cat .hg/clonebundles.manifest
  cat: .hg/clonebundles.manifest: No such file or directory
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
  pulling clonebundles manifest

  $ cat .hg/clonebundles.manifest
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2

A missing manifest results in the local file being deleted

  $ rm -f ../server/.hg/clonebundles.manifest
  $ hg --config hgmo.pullclonebundlesmanifest=true pull
  pulling from http://$LOCALHOST:$HGPORT/
  searching for changes
  no changes found
  deleting local clonebundles.manifest

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
