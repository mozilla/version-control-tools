  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m initial

  $ echo second > foo
  $ hg commit -m second

  $ echo third > foo
  $ hg commit -m 'Backed out changeset 6c9721b3b4df (bug 123)'

  $ hg -q push

No backout info on initial commit

  $ http http://localhost:$HGPORT/rev/55482a6fb4b1 --body-file body > /dev/null
  $ grep '<td>backs out' body
  [1]

No backout info on backed out commit (yet)

  $ http http://localhost:$HGPORT/rev/6c9721b3b4df --body-file body > /dev/null
  $ grep '<td>backs out' body
  [1]

Backout commit links to backed out commit

  $ http http://localhost:$HGPORT/rev/f8c8d5d22c7d --body-file body > /dev/null
  $ grep '<td>backs out' body
  <tr><td>backs out</td><td><a style="font-family: monospace" href="/rev/6c9721b3b4df">6c9721b3b4df</a></td></tr>
