  $ . $TESTDIR/hgext/bundleclone/tests/helpers.sh

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bundleclone = $TESTDIR/hgext/bundleclone
  > EOF

Create the server repo

  $ hg init server
  $ cd server
  $ touch foo
  $ hg -q commit -A -m 'add foo'
  $ touch bar
  $ hg -q commit -A -m 'add bar'

  $ hg serve -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Generate bundles with different compression

  $ hg -R server bundle --type gzip -a server.gz.hg
  2 changesets found
  $ hg -R server bundle --type bzip2 -a server.bz2.hg
  2 changesets found
  $ hg -R server bundle --type none -a server.uncompressed.hg
  2 changesets found

  $ cat > server/.hg/bundleclone.manifest << EOF
  > http://localhost:$HGPORT1/server.gz.hg compression=gzip
  > http://localhost:$HGPORT1/server.uncompressed.hg compression=none
  > http://localhost:$HGPORT1/server.bz2.hg compression=bzip2
  > EOF

Clone with no preferences should take the first item

  $ starthttpserver $HGPORT1
  $ hg clone -U http://localhost:$HGPORT/ clone-default
  downloading bundle http://localhost:$HGPORT1/server.gz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Preferring an unknown attribute should have no impact

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.prefers=foo=bar,baz=foo clone -U http://localhost:$HGPORT/ clone-unknown-attribute
  downloading bundle http://localhost:$HGPORT1/server.gz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Preferring bz2 compression will download a bzip2 bundle

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.prefers=compression=bzip2 clone -U http://localhost:$HGPORT/ clone-prefer-bz2
  downloading bundle http://localhost:$HGPORT1/server.bz2.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Preferring unknown value will fall back to second choice

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.prefers=compression=unknown,compression=none,compression=gzip clone -U http://localhost:$HGPORT/ clone-prefer-fallback
  downloading bundle http://localhost:$HGPORT1/server.uncompressed.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Having an order of preferences for a single attribute works

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.prefers=compression=none,compression=gzip,compression=bzip2 clone -U http://localhost:$HGPORT/ clone-multiple-values
  downloading bundle http://localhost:$HGPORT1/server.uncompressed.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Now let's add another axis of weighting. We use ec2region as a proxy for
hostname because this is a real use case.

  $ cp server.gz.hg us-west-1.server.gz.hg
  $ cp server.gz.hg us-east-1.server.gz.hg
  $ cp server.uncompressed.hg us-west-1.server.uncompressed.hg
  $ cp server.uncompressed.hg us-east-1.server.uncompressed.hg
  $ cp server.bz2.hg us-west-1.server.bz2.hg
  $ cp server.bz2.hg us-east-1.server.bz2.hg

  $ cat > server/.hg/bundleclone.manifest << EOF
  > http://localhost:$HGPORT1/us-west-1.server.gz.hg compression=gzip ec2region=us-west-1
  > http://localhost:$HGPORT1/us-east-1.server.gz.hg compression=gzip ec2region=us-east-1
  > http://localhost:$HGPORT1/us-west-1.server.uncompressed.hg compression=none ec2region=us-west-1
  > http://localhost:$HGPORT1/us-east-1.server.uncompressed.hg compression=none ec2region=us-east-1
  > http://localhost:$HGPORT1/us-west-1.server.bz2.hg compression=bzip2 ec2region=us-west-1
  > http://localhost:$HGPORT1/us-east-1.server.bz2.hg compression=bzip2 ec2region=us-east-1
  > EOF

Preferring just the compression level will take the first entry with
that value

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.prefers=compression=bzip2 clone -U http://localhost:$HGPORT/ clone-first-compression-entry
  downloading bundle http://localhost:$HGPORT1/us-west-1.server.bz2.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Preferring first the region then compression level gives an exact match

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.prefers=ec2region=us-east-1,compression=none clone -U http://localhost:$HGPORT/ clone-region-and-compression
  downloading bundle http://localhost:$HGPORT1/us-east-1.server.uncompressed.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Preferring a region that doesn't exist first will fall back to a known
region

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.prefers=ec2region=eu-west-1,ec2region=us-east-1,compression=bad,compression=bzip2 clone -U http://localhost:$HGPORT/ clone-unknown-primaries
  downloading bundle http://localhost:$HGPORT1/us-east-1.server.bz2.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found
