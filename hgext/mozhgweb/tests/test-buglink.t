  $ hg init repo
  $ cd repo
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mozhgweb = $TESTDIR/hgext/mozhgweb
  > EOF

Simple bug reference works

  $ echo initial > foo
  $ hg commit -A -m 'Bug 123456 - Initial commit'
  adding foo

  $ hg log -T '{desc|buglink}\n'
  <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=123456">Bug 123456</a> - Initial commit

Multiple bug references work

  $ echo multiple > foo
  $ hg commit -m 'Bug 1234 - Fix bug 456'
  $ hg log -r tip -T '{desc|buglink}\n'
  <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1234">Bug 1234</a> - Fix <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=456">bug 456</a>
