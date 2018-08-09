  $ cat >> $HGRCPATH <<EOF
  > [mozext]
  > headless = True
  > [extensions]
  > EOF
  $ echo "mozext=$(echo $TESTDIR)/hgext/mozext" >> $HGRCPATH

{bug} and {bugs} templates works

  $ hg init bugtest
  $ cd bugtest
  $ touch foo
  $ hg commit -A -m 'Bug 123456 - Test foo\nFixes bug 100245'
  adding foo
  $ hg log --template '{bug}\n'
  123456
  $ hg log --template '{join(bugs, " ")}\n'
  123456 100245

bug() revset works

  $ hg log -r 'bug(123456)' --template '{rev}\n'
  0
