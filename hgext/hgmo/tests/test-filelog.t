  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m 'Bug 314; r=calixte'
  $ echo second > foo
  $ cat > message << EOF
  > Bug 159 - Do foo; r=calixte
  > 
  > This is related to bug 265.
  > EOF
  $ hg commit -l message

  $ echo third > foo
  $ hg commit -m 'NO BUG'

  $ hg -q push

Single file with 3 commits

  $ http http://localhost:$HGPORT/log/tip/foo --body-file body > /dev/null
  $ grep -c '<br/>pushed <i>' body
  3
  $ grep -c '<br/>created <i>1970-01-01 00:00 +0000</i>' body
  3

Confirm no errors in log

  $ cat ../server/error.log
