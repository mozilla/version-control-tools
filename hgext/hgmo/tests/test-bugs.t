  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m 'Bug 123; r=gps'
  $ echo second > foo
  $ cat > message << EOF
  > Bug 456 - Do foo; r=gps
  > 
  > This is related to bug 789.
  > EOF
  $ hg commit -l message

  $ echo third > foo
  $ hg commit -m 'NO BUG'

  $ hg -q push

Single bug

  $ http http://localhost:$HGPORT/rev/b2695d7dbd02 --body-file body > /dev/null
  $ grep '<td>bugs' body
  <tr><td>bugs</td><td><a href="https://bugzilla.mozilla.org/show_bug.cgi?id=123">123</a></td></tr>

Multiple bugs separated by commas

  $ http http://localhost:$HGPORT/rev/2c0eb2e517f3 --body-file body > /dev/null
  $ grep '<td>bugs' body
  <tr><td>bugs</td><td><a href="https://bugzilla.mozilla.org/show_bug.cgi?id=456">456</a>, <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=789">789</a></td></tr>

No bug output if no bugs found

  $ http http://localhost:$HGPORT/rev/9295dbc456b5 --body-file body > /dev/null
  $ grep '<td>bugs' body
  [1]

Confirm no errors in log

  $ cat ../server/error.log
