  $ cat >> $HGRCPATH <<EOF
  > [mozext]
  > headless = True
  > backoutsearchlimit = 100
  > [extensions]
  > mozext = $TESTDIR/hgext/mozext
  > EOF

{backedoutby} templates works

  $ hg init backoutbytest
  $ cd backoutbytest
  $ touch foo
  $ hg commit -A -m 'Foo'
  adding foo
  $ touch bar
  $ hg commit -A -m 'Bar'
  adding bar
  $ hg backout -r tip -m "Backout 907f17e15674"
  removing bar
  changeset 2:47fdd3ef011e backs out changeset 1:907f17e15674
  $ hg log -r -2 --template '{backedoutby}\n'
  47fdd3ef011e5b86fe4ce90a88d362ac03361992
  $ hg log -r 2 --template '{join(backsoutnodes, " ")}\n'
  907f17e15674
