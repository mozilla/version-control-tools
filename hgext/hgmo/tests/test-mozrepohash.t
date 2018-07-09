  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > EOF

  $ hg init repo
  $ cd repo

Empty repo is hashable

  $ hg mozrepohash
  8d51358dfceb09704d3151dd72c0c94fd058ff4243cc015a1f973fe0a6dc8252

Repo with single changeset has a hash

  $ echo 0 > foo
  $ hg -q commit -A -m initial
  $ hg mozrepohash
  5619a72e8d3aa07ad84732ab8cd8595ae674b1b4f8798be96db0184ad7260b4a

Changing the phase changes the hash

  $ hg phase --public -r .
  $ hg mozrepohash
  e78b47275a3be33a4e327041c7734368e216f15498b52fd6df06cfabbe0c6197

Adding a bookmark changes the hash

  $ hg book mymark
  $ hg mozrepohash
  cd51f5673cb73bfa6f2768865ad7666e45179796ddc142a5739ea81b3862eb4d
