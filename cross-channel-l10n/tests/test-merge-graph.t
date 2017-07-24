test complex graph creating a non-linear sparse history

  $ hg init r
  $ cd r

Root commit

  $ mkdir red
  $ mkdir green
  $ echo base >> red/base
  $ echo base >> green/base
  $ hg addremove -q
  $ hg ci -m'0'

Create forks and merges

  $ for i in `seq 4`; do
  $ hg co -qr 0
  $ echo red$i >> red/red$i
  $ hg addremove -q
  $ hg ci -m$i -q
  $ done
  $ hg co -qr 3
  $ echo green >> green/green1
  $ hg addremove -q
  $ hg ci -m5 -q
  $ hg log -G -T '{ rev }: { files }\n'
  @  5: green/green1
  |
  | o  4: red/red4
  | |
  o |  3: red/red3
  |/
  | o  2: red/red2
  |/
  | o  1: red/red1
  |/
  o  0: green/base red/base
  
  $ hg co -qr 1
  $ hg merge -q -r 2
  $ hg ci -m 6
  $ hg co -qr 5
  $ hg merge -q -r 4
  $ hg ci -m7 -q
  $ hg merge -q -r 6
  $ hg ci -m8 -q
  $ echo more >> red/base
  $ hg ci -m9 -q

Ensure that we merged everything, should only have a single head
  $ hg heads -T '{ rev }\n'
  9


  >>> from mercurial.hg import repository
  >>> from mercurial.ui import ui
  >>> from mozxchannel import graph
  >>> repo = repository(ui())
  >>> len(repo)
  10
  >>> g = graph.SparseGraph(repo, ['filelog("glob:red/*")'])
  >>> g.createGraph()
  >>> sorted(g.parents.keys())
  [0, 1, 2, 3, 4, 9]
  >>> sorted(g.parents[9])  # all initial forks are parents
  [1, 2, 3, 4]
