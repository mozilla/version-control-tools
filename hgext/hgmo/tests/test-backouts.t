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

  $ grep x2620 body
  <a href="/">Mercurial</a>  / changeset / 6c9721b3b4df &#x2620;
  <tr><td colspan="2" style="background:#ff3333;"><strong>&#x2620;&#x2620; backed out by <a style="font-family: monospace" href="/rev/f8c8d5d22c7d">f8c8d5d22c7d</a> &#x2620; &#x2620;</strong></td></tr>

Backout commit links to backed out commit

  $ http http://localhost:$HGPORT/rev/f8c8d5d22c7d --body-file body > /dev/null
  $ grep '<td>backs out' body
  <tr><td>backs out</td><td><a style="font-family: monospace" href="/rev/6c9721b3b4df">6c9721b3b4df</a></td></tr>

Reference a backed out node that doesn't exist (bug 1257152)

  $ hg -q up -r 0
  $ echo badnode > foo
  $ hg commit -m 'Backed out changeset deadbeefbead (bug 123)'
  created new head
  $ hg -q push -f

  $ http http://localhost:$HGPORT/rev/bdfc7e1edbe7 --body-file body > /dev/null
  $ grep 'unknown revision' body
  [1]

  $ grep 'backs out' body
  [1]
