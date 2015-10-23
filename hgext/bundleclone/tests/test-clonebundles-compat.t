  $ . $TESTDIR/hgext/bundleclone/tests/helpers.sh

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bundleclone = $TESTDIR/hgext/bundleclone
  > EOF

  $ hg init server
  $ cd server
  $ touch foo
  $ hg -q commit -A -m 'add foo'
  $ touch bar
  $ hg -q commit -A -m 'add bar'

TODO use explicit 3.6+ version when available
  $ $TESTDIR/venv/mercurials/@/bin/hg --config extensions.clonebundles= serve -d -p $HGPORT --pid-file hg.pid -A access.log -E error.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Both bundleclone and clonebundles should be advertised if their
manifest files are present

  $ touch server/.hg/bundleclone.manifest
  $ touch server/.hg/clonebundles.manifest

A modern client will say it supports built-in clonebundles feature and
will use it

#if hg36+
  $ hg -v clone -U http://localhost:$HGPORT empty-manifest-file
  (mercurial client has built-in support for bundle clone features; the "bundleclone" extension can likely safely be removed)
  (but the experimental.clonebundles config flag is not enabled: enable it before disabling bundleclone or cloning from pre-generated bundles may not work)
  no clone bundles available on remote; falling back to regular clone
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files

  $ hg -v --config experimental.clonebundles=True clone -U http://localhost:$HGPORT empty-manifest-2
  (mercurial client has built-in support for bundle clone features; the "bundleclone" extension can likely safely be removed)
  no clone bundles available on remote; falling back to regular clone
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files

An older client will use bundleclone facility
#else

  $ hg -v clone -U http://localhost:$HGPORT empty-manifest-file
  no bundles available; using normal clone
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
#endif

Actually doing a clone bundle will work with built-in feature

  $ cat >> $HGRCPATH << EOF
  > [experimental]
  > clonebundles = true
  > EOF

  $ hg -R server bundle --type gzip --all fullgz.hg
  2 changesets found

  $ cat > server/.hg/clonebundles.manifest << EOF
  > http://localhost:$HGPORT1/fullgz.hg BUNDLESPEC=gzip-v1
  > EOF

  $ cat > server/.hg/bundleclone.manifest << EOF
  > http://localhost:$HGPORT1/fullgz.hg compression=gzip
  > EOF

  $ starthttpserver $HGPORT1

#if hg36+
  $ hg clone -U http://localhost:$HGPORT clone-full
  (mercurial client has built-in support for bundle clone features; the "bundleclone" extension can likely safely be removed)
  applying clone bundle from http://localhost:$HGPORT1/fullgz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finished applying clone bundle
  searching for changes
  no changes found

#else

  $ hg clone -U http://localhost:$HGPORT clone-full
  downloading bundle http://localhost:$HGPORT1/fullgz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

#endif


Clone will copy both manifests from the server
(We only care about this on modern clients because we only care about
this on the server, which is a modern version.)
#if hg33+
  $ starthttpserver $HGPORT1

  $ hg --config bundleclone.pullmanifest=true clone -U http://localhost:$HGPORT clone-copy-manifest | grep pulling
  * (glob)
  pulling bundleclone manifest
  pulling clonebundles manifest

  $ cat clone-copy-manifest/.hg/bundleclone.manifest
  http://localhost:$HGPORT1/fullgz.hg compression=gzip

  $ cat clone-copy-manifest/.hg/clonebundles.manifest
  http://localhost:$HGPORT1/fullgz.hg BUNDLESPEC=gzip-v1

#endif

Stream bundles support. bundleclone and clonebundles use slightly
different stream bundles formats. The latter has a more formal format
with different file headers.

  $ hg -R server streambundle stream-legacy.hg
  writing stream-legacy.hg
  stream bundle file written successully.
  include the following in its manifest entry:
  stream=revlogv1

  $ cat > server/.hg/bundleclone.manifest << EOF
  > http://localhost:$HGPORT1/stream-legacy.hg stream=revlogv1
  > EOF

  $ hg -R server streambundle --type s1 stream-s1.hg
  writing 613 bytes for 4 files
  bundle requirements: revlogv1

  $ cat > server/.hg/clonebundles.manifest << EOF
  > http://localhost:$HGPORT1/stream-s1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1
  > EOF

  $ starthttpserver $HGPORT1

#if hg36+
  $ hg clone -U http://localhost:$HGPORT stream-bundle
  (mercurial client has built-in support for bundle clone features; the "bundleclone" extension can likely safely be removed)
  applying clone bundle from http://localhost:$HGPORT1/stream-s1.hg
  4 files to transfer, 613 bytes of data
  transferred 613 bytes in *.* seconds (*) (glob)
  finished applying clone bundle
  searching for changes
  no changes found

#else
  $ hg clone -U http://localhost:$HGPORT stream-legacy
  downloading bundle http://localhost:$HGPORT1/stream-legacy.hg
  streaming all changes
  4 files to transfer, 613 bytes of data
  transferred 613 bytes in * seconds (*) (glob)
  finishing applying bundle; pulling
  searching for changes
  no changes found

#endif

Hacked up clonebundles extension should fail on 3.6+

  $ $TESTDIR/venv/mercurials/@/bin/hg --config extensions.clonebundles=$TESTDIR/hgserver/clonebundles.py version
  abort: use built-in clonebundles extension with Mercurial 3.6+
  [255]
