  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Extension works with default config

  $ hg robustcheckout http://localhost:$HGPORT/bad-server good-clone --revision 94086d65796f
  ensuring http://localhost:$HGPORT/bad-server@94086d65796f is available at good-clone
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  searching for changes
  no changes found
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 94086d65796fd7fc8f957a2c5548db17a13f1f1f

Server abort part way through response is handled
TODO not yet implemented properly

  $ cp -a server/bad-server server/bad-server-bytelimit

  $ cat >> server/bad-server-bytelimit/.hg/hgrc << EOF
  > [badserver]
  > bytelimit = 11
  > EOF

  $ hg robustcheckout http://localhost:$HGPORT/bad-server-bytelimit byte-limit --revision 94086d65796f
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from existing pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  searching for changes
  no changes found
  abort: stream ended unexpectedly (got 3 bytes, expected 4)
  [255]
