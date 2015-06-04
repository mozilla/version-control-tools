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
  <tr><td>reviewers</td><td>gps</td></tr>

Multiple reviewers separated by comma

  $ http http://localhost:$HGPORT/rev/e32726f11326 --body-file body > /dev/null
  $ grep '<td>reviewers' body
  <tr><td>reviewers</td><td>gps, smacleod</td></tr>

No reviewer output if no reviewers

  $ http http://localhost:$HGPORT/rev/f081f6d27c72 --body-file body > /dev/null
  $ grep '<td>reviewers' body
  [1]
