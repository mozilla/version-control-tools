  $ hg init server
  $ cat >> server/.hg/hgrc << EOF
  > [extensions]
  > blackbox =
  > [blackbox]
  > track = *
  > EOF

  $ hg -q clone server client
  $ cd client

  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

No tags cache should exist because there is no .hgtags file

  $ [ -f ../server/.hg/cache/hgtagsfnodes1 ]
  [1]

Pushing a tag should not populate the tags cache unless without the hook

  $ hg tag initial
  $ hg -q push

  $ [ -f ../server/.hg/cache/hgtagsfnodes1 ]
  [1]

  $ cat ../server/.hg/blackbox.log
  *> updated base branch cache in * seconds (glob)
  *> wrote base branch cache with 1 labels and 1 nodes (glob)
  *> 1 incoming changes - new heads: 96ee1d7354c4 (glob)
  *> updated base branch cache in * seconds (glob)
  *> wrote base branch cache with 1 labels and 1 nodes (glob)
  *> 1 incoming changes - new heads: 5e849d85a748 (glob)

Activating the hook causes tags cache to get populated

  $ cat >> ../server/.hg/hgrc << EOF
  > [hooks]
  > pretxnclose.populate_caches = python:mozhghooks.populate_caches.hook
  > EOF

  $ hg tag newtag
  $ hg -q push

  $ [ -f ../server/.hg/cache/hgtagsfnodes1 ]

  $ tail -10 ../server/.hg/blackbox.log
  *> 1 incoming changes - new heads: 5e849d85a748 (glob)
  *> updated base branch cache in * seconds (glob) (?)
  *> wrote base branch cache with 1 labels and 1 nodes (glob) (?)
  *> writing 72 bytes to cache/hgtagsfnodes1 (glob)
  *> 0/1 cache hits/lookups in * seconds (glob)
  *> writing .hg/cache/tags2-served with 2 tags (glob)
  *> 1/1 cache hits/lookups in * seconds (glob)
  *> writing .hg/cache/tags2 with 2 tags (glob)
  *> pythonhook-pretxnclose: mozhghooks.populate_caches.hook finished in * seconds (glob)
  *> updated base branch cache in * seconds (glob) (?)
  *> wrote base branch cache with 1 labels and 1 nodes (glob) (?)
  *> 1 incoming changes - new heads: cf120f74c0ec (glob)
