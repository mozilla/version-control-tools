  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF
  $ cd ..

  $ export USER=user1@example.com
  $ hg -q clone server client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg -q push
  recorded push in pushlog
  $ echo second > foo
  $ hg commit -m second
  $ echo third > foo
  $ hg commit -m third
  $ export USER=user2@example.com
  $ hg -q push
  recorded push in pushlog

  $ cd ../server

{pushid} shows the push id

  $ hg log -T '{rev} {pushid}\n'
  2 2
  1 2
  0 1

{pushuser} shows who did the push

  $ hg log -T '{rev} {pushuser}\n'
  2 user2@example.com
  1 user2@example.com
  0 user1@example.com

{pushdate} shows when the push happened

  $ hg log -T '{rev} {date(pushdate, "%Y")}\n'
  2 \d{4} (re)
  1 \d{4} (re)
  0 \d{4} (re)

{pushbasenode} shows the base node from the push

  $ hg log -T '{rev} {node|short} {pushbasenode}\n'
  2 82f53df85e9f 6c9721b3b4dfc8c1f2d3103595e8bb2ffe5b8ff2
  1 6c9721b3b4df 6c9721b3b4dfc8c1f2d3103595e8bb2ffe5b8ff2
  0 55482a6fb4b1 55482a6fb4b1881fa8f746fd52cf6f096bb21c89

{pushheadnode} shows the head node from the push

  $ hg log -T '{rev} {node|short} {pushheadnode}\n'
  2 82f53df85e9f 82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce
  1 6c9721b3b4df 82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce
  0 55482a6fb4b1 55482a6fb4b1881fa8f746fd52cf6f096bb21c89

Test autolanded pushes

  $ cd ../client
  $ export USER=bind-autoland@mozilla.com
  $ export AUTOLAND_REQUEST_USER=user3@example.com
  $ echo autoland > foo
  $ hg commit -m autoland
  $ hg -q push
  autoland or landing worker push detected
  recorded push in pushlog

Test landing worker pushes

  $ export USER=lando_landing_worker@mozilla.com
  $ export AUTOLAND_REQUEST_USER=user4@example.com
  $ echo somethingsomething > foo
  $ hg commit -m "landing worker" 
  $ hg -q push
  autoland or landing worker push detected
  recorded push in pushlog

Test landing worker (dev) pushes

  $ export USER=lando_landing_worker_dev@mozilla.com
  $ export AUTOLAND_REQUEST_USER=user4@example.com
  $ echo somethingsomethingsomething > foo
  $ hg commit -m "landing worker" 
  $ hg -q push
  autoland or landing worker push detected
  recorded push in pushlog

  $ cd ../server

{pushuser} shows who did the push

  $ hg log -T '{rev} {pushuser}\n'
  5 user4@example.com
  4 user4@example.com
  3 user3@example.com
  2 user2@example.com
  1 user2@example.com
  0 user1@example.com
