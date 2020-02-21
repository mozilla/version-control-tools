test simple graph creating a sparse linear history

  $ hg init r
  $ cd r

Root commit

  $ echo red1 >> red
  $ hg add red
  $ hg ci -m'red0'

Create forks and merges

  $ for i in `seq 3`; do
  $ echo red$i >> red
  $ hg ci -mred$i
  $ hg co -qr desc\("red$(( $i - 1 ))"\)
  $ echo green >> green
  $ hg addremove -q
  $ hg ci -qmgreen$i
  $ hg merge -q
  $ hg ci -qmmerge$i
  $ done
  $ hg log -G -T '{ rev }: { files }\n'
  @    9:
  |\
  | o  8: green
  | |
  o |  7: red
  | |
  o |  6:
  |\|
  o |  5: green
  | |
  | o  4: red
  | |
  | o  3:
  |/|
  | o  2: green
  | |
  o |  1: red
  |/
  o  0: red
  


  >>> from mercurial.hg import repository
  >>> from mercurial.ui import ui
  >>> from mozxchannel import graph
  >>> repo = repository(ui())
  >>> len(repo)
  10
  >>> g = graph.SparseGraph(repo, [b'filelog("red")'])
  >>> g.createGraph()
  >>> sorted(g.parents.keys())
  [0, 1, 4, 7]
  >>> sorted(g.parents[0])
  []
  >>> sorted(g.parents[1])
  [0]
  >>> sorted(g.parents[7])
  [4]
  >>> g.roots
  [0]
  >>> sorted(g.heads)
  [7]
  >>> g = graph.SparseGraph(repo, [b'filelog("red") and 2::'])
  >>> g.createGraph()
  >>> sorted(g.parents.keys())
  [4, 7]

Now let's test the unoptimized graph. Fixing the artifacts below would be nice.

  >>> from mercurial.hg import repository
  >>> from mercurial.ui import ui
  >>> from mozxchannel import graph
  >>> repo = repository(ui())
  >>> g = graph.SparseGraph(repo, [b'filelog("red")'])
  >>> g.createGraph(max_depth=0, optimize=False)
  >>> sorted(g.parents.keys())
  [0, 1, 4, 7]
  >>> sorted(g.parents[0])
  []
  >>> sorted(g.parents[1])
  [0]
  >>> sorted(g.parents[7])  # this also shows the route 1, 5, 6, 7
  [1, 4]
  >>> g.roots
  [0]
  >>> sorted(g.heads)
  [7]

Test a partial graph

  >>> from mercurial.hg import repository
  >>> from mercurial.ui import ui
  >>> from mozxchannel import graph
  >>> repo = repository(ui())
  >>> g = graph.SparseGraph(repo, [2, 3, 4])
  >>> g.createGraph()
  >>> print(sorted(g.parents[2]))
  []
