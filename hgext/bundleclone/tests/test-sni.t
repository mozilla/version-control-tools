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

Generate bundle

  $ hg -R server bundle --type gzip -a server-sni.gz.hg
  2 changesets found
  $ hg -R server bundle --type gzip -a server-nosni.gz.hg
  2 changesets found

Require SNI works if Python version is new enough

  $ cat > server/.hg/bundleclone.manifest << EOF
  > http://localhost:$HGPORT1/server-sni.gz.hg compression=gzip requiresni=true
  > EOF

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.fakepyver=2,7,10 clone -U http://localhost:$HGPORT/ clone-working-sni
  downloading bundle http://localhost:$HGPORT1/server-sni.gz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Old Python without SNI fails with no non-SNI URL

  $ hg --config bundleclone.fakepyver=2,7,8 clone -U http://localhost:$HGPORT/ clone-no-sni
  (your Python is older than 2.7.9 and does not support modern and secure SSL/TLS; please consider upgrading your Python to a secure version)
  (ignoring URL on server that requires SNI)
  abort: no appropriate bundles available
  (you may wish to complain to the server operator)
  [255]

Old Mercurial without SNI fails with no non-SNI URL

  $ hg --config bundleclone.fakehgver=3,0 clone -U http://localhost:$HGPORT/ clone-no-hg-sni
  (you Mercurial is old and does not support modern and secure SSL/TLS; please consider upgrading your Mercurial to 3.3+ which supports modern and secure SSL/TLS
  (ignoring URL on server that requires SNI)
  abort: no appropriate bundles available
  (you may wish to complain to the server operator)
  [255]

Old Python and old Mercurial messages are printed

  $ hg --config bundleclone.fakepyver=2,7,3 --config bundleclone.fakehgver=3,0 clone -U http://localhost:$HGPORT/ clone-old-python-old-mercurial
  (your Python is older than 2.7.9 and does not support modern and secure SSL/TLS; please consider upgrading your Python to a secure version)
  (you Mercurial is old and does not support modern and secure SSL/TLS; please consider upgrading your Mercurial to 3.3+ which supports modern and secure SSL/TLS
  (ignoring URL on server that requires SNI)
  abort: no appropriate bundles available
  (you may wish to complain to the server operator)
  [255]

Old Python without SNI filters SNI URLs

  $ cat > server/.hg/bundleclone.manifest << EOF
  > http://localhost:$HGPORT1/server-sni.gz.hg compression=gzip requiresni=true
  > http://localhost:$HGPORT1/server-nosni.gz.hg compression=gzip
  > EOF

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.fakepyver=2,7,8 clone -U http://localhost:$HGPORT/ clone-no-sni-fallback
  (your Python is older than 2.7.9 and does not support modern and secure SSL/TLS; please consider upgrading your Python to a secure version)
  (ignoring URL on server that requires SNI)
  downloading bundle http://localhost:$HGPORT1/server-nosni.gz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

Old Mercurial without SNI filters SNI URLs

  $ starthttpserver $HGPORT1
  $ hg --config bundleclone.fakehgver=3,0 clone -U http://localhost:$HGPORT/ clone-old-hg-fallback
  (you Mercurial is old and does not support modern and secure SSL/TLS; please consider upgrading your Mercurial to 3.3+ which supports modern and secure SSL/TLS
  (ignoring URL on server that requires SNI)
  downloading bundle http://localhost:$HGPORT1/server-nosni.gz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found

requiresni=false works

  $ cat > server/.hg/bundleclone.manifest << EOF
  > http://localhost:$HGPORT1/server-nosni.gz.hg compression=gzip requiresni=false
  > EOF

  $ starthttpserver $HGPORT1
  $ hg clone -U http://localhost:$HGPORT/ clone-sni-false
  downloading bundle http://localhost:$HGPORT1/server-nosni.gz.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  finishing applying bundle; pulling
  searching for changes
  no changes found
