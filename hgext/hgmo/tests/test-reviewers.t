  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m 'Bug 123; r=gps'
  $ echo second > foo
  $ hg commit -m 'Bug 456; r=gps, smacleod'
  $ echo third > foo
  $ hg commit -m 'NO BUG NO REVIEWER'
  $ hg -q push

Single reviewer works

  $ http http://localhost:$HGPORT/rev/b2695d7dbd02 --body-file body > /dev/null
  $ grep '<td>reviewers' body
  <tr><td>reviewers</td><td><a href="/log?rev=reviewer%28gps%29&revcount=50">gps</a></td></tr>

Multiple reviewers separated by comma

  $ http http://localhost:$HGPORT/rev/e32726f11326 --body-file body > /dev/null
  $ grep '<td>reviewers' body
  <tr><td>reviewers</td><td><a href="/log?rev=reviewer%28gps%29&revcount=50">gps</a>, <a href="/log?rev=reviewer%28smacleod%29&revcount=50">smacleod</a></td></tr>

No reviewer output if no reviewers

  $ http http://localhost:$HGPORT/rev/f081f6d27c72 --body-file body > /dev/null
  $ grep '<td>reviewers' body
  [1]

Reviewer revset works

  $ http http://localhost:$HGPORT/log?rev=reviewer%28gps%29 --body-file body > /dev/null
  $ grep '<a href="/rev/' body
  <a href="/rev/e32726f11326">diff</a><br/>
  <a href="/rev/b2695d7dbd02">diff</a><br/>
