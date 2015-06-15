  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > buglink = $TESTDIR/hgext/pushlog-legacy/buglink.py
  > pushlog = $TESTDIR/hgext/pushlog
  > 
  > [web]
  > templates = $TESTDIR/hgtemplates
  > style = gitweb_mozilla
  > EOF

  $ alias http=$TESTDIR/testing/http-request.py

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
  $ hg serve -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

Push info should show up in changeset view

  $ http http://localhost:$HGPORT/rev/55482a6fb4b1 --body-file body > /dev/null
  $ grep push body
  <a href="/pushloghtml">pushlog</a> |
  <tr><td>push id</td><td><a href="/pushloghtml?changeset=55482a6fb4b1">1</a></td></tr>
  <tr><td>push user</td><td>user1@example.com</td></tr>
  <tr><td>push date</td><td>*</td></tr> (glob)

  $ http http://localhost:$HGPORT/rev/6c9721b3b4df --body-file body > /dev/null
  $ grep push body
  <a href="/pushloghtml">pushlog</a> |
  <tr><td>push id</td><td><a href="/pushloghtml?changeset=6c9721b3b4df">2</a></td></tr>
  <tr><td>push user</td><td>user2@example.com</td></tr>
  <tr><td>push date</td><td>*</td></tr> (glob)

  $ http http://localhost:$HGPORT/log --body-file body > /dev/null
  $ grep push body
  <a href="/pushloghtml">pushlog</a> |
  Push <a href="/pushloghtml?changeset=82f53df85e9f">2</a> by user2@example.com at *<br /> (glob)
  Push <a href="/pushloghtml?changeset=6c9721b3b4df">2</a> by user2@example.com at *<br /> (glob)
  Push <a href="/pushloghtml?changeset=55482a6fb4b1">1</a> by user1@example.com at *<br /> (glob)
