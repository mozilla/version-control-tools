  $ . $TESTDIR/hgext/robustcheckout/tests/helpers.sh

Extension works with default config

  $ hg robustcheckout http://$LOCALHOST:$HGPORT/bad-server good-clone --revision 94086d65796f
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server@94086d65796f is available at good-clone
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  transferred 723 bytes in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  searching for changes
  new changesets 96ee1d7354c4:94086d65796f (?)
  no changes found
  new changesets 96ee1d7354c4:94086d65796f (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 94086d65796fd7fc8f957a2c5548db17a13f1f1f

Connecting to non-running server fails

  $ hg robustcheckout http://$LOCALHOST:$HGPORT1/repo0 no-server --revision 94086d65796f --networkattempts 2
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT1/repo0@94086d65796f is available at no-server
  socket error: [Errno 111] Connection refused
  (retrying after network failure on attempt 1 of 2)
  (waiting *s before retry) (glob)
  ensuring http://$LOCALHOST:$HGPORT1/repo0@94086d65796f is available at no-server
  socket error: [Errno 111] Connection refused
  abort: reached maximum number of network attempts; giving up
   (hg46 !)
  [255]

Server abort part way through response results in retries

  $ cp -a server/bad-server server/bad-server-bytelimit

#if hg46
  $ cat >> server/bad-server-bytelimit/.hg/hgrc << EOF
  > [badserver]
  > bytelimit = 500
  > EOF
#else
  $ cat >> server/bad-server-bytelimit/.hg/hgrc << EOF
  > [badserver]
  > bytelimit = 11
  > EOF
#endif

  $ hg robustcheckout http://$LOCALHOST:$HGPORT/bad-server-bytelimit byte-limit --revision 94086d65796f --sharebase $TESTTMP/bad-server-share
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  stream ended unexpectedly  (got 244 bytes, expected 816)
  (retrying after network failure on attempt 1 of 3)
  (waiting *s before retry) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  stream ended unexpectedly  (got 244 bytes, expected 816)
  (retrying after network failure on attempt 2 of 3)
  (waiting *s before retry) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  \r (no-eol) (esc)
  clone [                                                               ]   0/723\r (no-eol) (esc)
                                                                                  \r (no-eol) (esc)
  stream ended unexpectedly  (got 244 bytes, expected 816)
  abort: reached maximum number of network attempts; giving up
  
  [255]

Adjusting the network limit works

  $ hg robustcheckout http://$LOCALHOST:$HGPORT/bad-server-bytelimit byte-limit --networkattempts 2 --revision 94086d65796f --sharebase $TESTTMP/bad-server-share
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  stream ended unexpectedly  (got 244 bytes, expected 816)
  (retrying after network failure on attempt 1 of 2)
  (waiting *s before retry) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  stream ended unexpectedly  (got 244 bytes, expected 816)
  abort: reached maximum number of network attempts; giving up
  
  [255]

Recovering server will result in good clone

  $ echo 6 > server/bad-server-bytelimit/.hg/badserveruntilgood

  $ hg robustcheckout http://$LOCALHOST:$HGPORT/bad-server-bytelimit byte-limit --revision 94086d65796f --sharebase $TESTTMP/bad-server-share
  (using Mercurial *) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  stream ended unexpectedly  (got 244 bytes, expected 816)
  (retrying after network failure on attempt 1 of 3)
  (waiting *s before retry) (glob)
  ensuring http://$LOCALHOST:$HGPORT/bad-server-bytelimit@94086d65796f is available at byte-limit
  (sharing from new pooled repository 96ee1d7354c4ad7372047672c36a1f561e3a6a4c)
  streaming all changes
  6 files to transfer, 723 bytes of data
  transferred 723 bytes in \d+\.\d+ seconds \(\d+(\.\d+)? KB/sec\) (re)
  new changesets 96ee1d7354c4:94086d65796f (?)
  searching for changes
  new changesets 96ee1d7354c4:94086d65796f (?)
  no changes found
  \r (no-eol) (esc) (?)
  updating [===============================================================>] 1/1\r (no-eol) (esc) (?)
                                                                                  \r (no-eol) (esc) (?)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to 94086d65796fd7fc8f957a2c5548db17a13f1f1f

Confirm no errors in log

  $ cat ./server/error.log
