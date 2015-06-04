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

Backed out commits should show warnings

  $ http http://localhost:$HGPORT/rev/6c9721b3b4df --body-file body > /dev/null
  $ grep '<td>backs out' body
  [1]

  $ grep x1f4a9 body
  <a href="/">Mercurial</a>  / changeset / 6c9721b3b4df &#x1f4a9;
  <tr><td><strong>&#x1f4a9;&#x1f4a9; backed out by <a style="font-family: monospace" href="/rev/f8c8d5d22c7d">f8c8d5d22c7d</a> &#x1f4a9; &#x1f4a9;</strong></td></tr>

Backout commit links to backed out commit

  $ http http://localhost:$HGPORT/rev/f8c8d5d22c7d --body-file body > /dev/null
  $ grep '<td>backs out' body
  <tr><td>backs out</td><td><a style="font-family: monospace" href="/rev/6c9721b3b4df">6c9721b3b4df</a></td></tr>
