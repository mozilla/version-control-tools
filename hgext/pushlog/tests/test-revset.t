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
  Trying to insert into pushlog.
  Inserted into the pushlog db successfully.
  $ echo second > foo
  $ hg commit -m second
  $ echo third > foo
  $ hg commit -m third
  $ export USER=user2@example.com
  $ hg -q push
  Trying to insert into pushlog.
  Inserted into the pushlog db successfully.

  $ cd ../server

pushhead() fails with an argument

  $ hg log -r 'pushhead(foo)' -T '{rev}\n'
  hg: parse error: pushhead takes no arguments
  [255]

pushhead() returns expected results

  $ hg log -r 'pushhead()' -T '{rev}\n'
  0
  2

pushdate() requires a string argument

  $ hg log -r 'pushdate()'
  hg: parse error: pushdate requires one argument
  [255]

pushdate() filters appropriately

  $ hg log -r 'pushdate(yesterday)'

  $ hg log -r 'pushdate(today)' -T '{rev}\n'
  0
  1
  2

  $ hg log -r 'pushdate("yesterday to today")' -T '{rev}\n'
  0
  1
  2

pushuser() requires an argument

  $ hg log -r 'pushuser()'
  hg: parse error: pushuser requires one argument
  [255]

pushuser() on unknown user returns null set

  $ hg log -r 'pushuser(unknown)'

pushuser() matches full username

  $ hg log -r 'pushuser(user1@example.com)' -T '{rev}\n'
  0

  $ hg log -r 'pushuser(user2@example.com)' -T '{rev}\n'
  1
  2

pushuser() matches partial user

  $ hg log -r 'pushuser(@example.com)' -T '{rev}\n'
  0
  1
  2

pushuser() does regex matching

  $ hg log -r 'pushuser("re:user1")' -T '{rev}\n'
  0

pushuser() matching is case insensitive

  $ hg log -r 'pushuser(user2@EXAMPLE.COM)' -T '{rev}\n'
  1
  2
