  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ mkdir config
  $ cat > config/milestone.txt << EOF
  > # Some comments
  > 14.0
  > EOF
  $ hg -q commit -A -m 'milestone 14.0'

  $ echo third > foo
  $ hg commit -m third

  $ hg -q push

No milestone output if there is no config/milestone.txt file

  $ http http://localhost:$HGPORT/rev/55482a6fb4b1 --body-file body > /dev/null
  $ grep '<td>milestone' body
  [1]

Introduction of milestone should show value

  $ http http://localhost:$HGPORT/rev/3905e294b147 --body-file body > /dev/null
  $ grep '<td>milestone' body
  <tr><td>milestone</td><td>14.0</td></tr>

Commit not changing milestone should show milestone

  $ http http://localhost:$HGPORT/rev/5e06103db78f --body-file body > /dev/null
  $ grep '<td>milestone' body
  <tr><td>milestone</td><td>14.0</td></tr>

Confirm no errors in log

  $ cat ../server/error.log
