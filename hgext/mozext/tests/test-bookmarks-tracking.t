  $ cat >> $HGRCPATH <<EOF
  > [mozext]
  > headless = True
  > [extensions]
  > EOF
  $ echo "mozext=$(echo $TESTDIR)/hgext/mozext" >> $HGRCPATH

Test prunerelbranches commands works

  $ hg init test
  $ cd test
  $ touch foo
  $ hg commit -A -m 'test foo'
  adding foo
  $ hg bookmark release/MOBILE80_2011100517_RELBRANCH
  $ hg bookmark foobar
  $ echo 1 > foo
  $ hg commit -m 'commit on bookmark'
  $ hg bookmarks
   * foobar                    1:619600a1d332
     release/MOBILE80_2011100517_RELBRANCH 0:56eeeaf5261d
  $ hg prunerelbranches
  Removing bookmark release/MOBILE80_2011100517_RELBRANCH
  $ hg bookmarks
   * foobar                    1:619600a1d332
