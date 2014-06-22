  $ hg init
  $ cat > .hg/hgrc << EOF
  > [diff]
  > nodates = 1
  > [extensions]
  > mq =
  > mqobs = $TESTDIR/hgext/mqobs
  > EOF

  $ hg init --mq
  $ echo 'initial' > foo
  $ hg commit -A -m 'initial'
  adding foo

qrefresh will write an obsolete marker

  $ echo 'qpatch1' > foo
  $ hg qnew qpatch1 -m 'first patch' -d '0 0'
  $ echo 'revise patch' > foo
  $ hg qrefresh -d '0 0'
  $ hg debugobsolete
  ac48f84d31b1c26916c866f2609bc2b3f3e62b6a 7222d6b84fec7ccf8d6c093b921732b38f260677 0 {'date': '(0.0, 0)', 'user': 'test'}
  $ hg qpop
  popping qpatch1
  patch queue now empty

qpush still works fine

  $ hg qpush
  applying qpatch1
  now at: qpatch1
  $ hg qpop
  popping qpatch1
  patch queue now empty
