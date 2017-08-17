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

Connecting to non-running server fails

  $ hg robustcheckout http://localhost:$HGPORT1/repo0 no-server --revision 94086d65796f --networkattempts 2
  ensuring http://localhost:$HGPORT1/repo0@94086d65796f is available at no-server
  socket error: [Errno 111] Connection refused
  (retrying after network failure on attempt 1 of 2)
  (waiting *s before retry) (glob)
  ensuring http://localhost:$HGPORT1/repo0@94086d65796f is available at no-server
  socket error: [Errno 111] Connection refused
  abort: reached maximum number of network attempts; giving up
  
  [255]

Server abort part way through response results in retries

  $ cp -a server/bad-server server/bad-server-bytelimit

  $ cat >> server/bad-server-bytelimit/.hg/hgrc << EOF
  > [badserver]
  > bytelimit = 11
  > EOF

  $ hg robustcheckout http://localhost:$HGPORT/bad-server-bytelimit byte-limit --revision 94086d65796f --sharebase $TESTTMP/bad-server-share
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  requesting all changes
  stream ended unexpectedly (got 0 bytes, expected 4)
  (retrying after network failure on attempt 1 of 3)
  (waiting *s before retry) (glob)
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  requesting all changes
  stream ended unexpectedly (got 0 bytes, expected 4)
  (retrying after network failure on attempt 2 of 3)
  (waiting *s before retry) (glob)
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  requesting all changes
  stream ended unexpectedly (got 0 bytes, expected 4)
  abort: reached maximum number of network attempts; giving up
  
  [255]

Adjusting the network limit works

  $ hg robustcheckout http://localhost:$HGPORT/bad-server-bytelimit byte-limit --networkattempts 2 --revision 94086d65796f --sharebase $TESTTMP/bad-server-share
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  requesting all changes
  stream ended unexpectedly (got 0 bytes, expected 4)
  (retrying after network failure on attempt 1 of 2)
  (waiting *s before retry) (glob)
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  requesting all changes
  stream ended unexpectedly (got 0 bytes, expected 4)
  abort: reached maximum number of network attempts; giving up
  
  [255]

Recovering server will result in good clone

  $ echo 6 > server/bad-server-bytelimit/.hg/badserveruntilgood

  $ hg robustcheckout http://localhost:$HGPORT/bad-server-bytelimit byte-limit --revision 94086d65796f --sharebase $TESTTMP/bad-server-share
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  requesting all changes
  stream ended unexpectedly (got 0 bytes, expected 4)
  (retrying after network failure on attempt 1 of 3)
  (waiting *s before retry) (glob)
  ensuring http://localhost:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
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
