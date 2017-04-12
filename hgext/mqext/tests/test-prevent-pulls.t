  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > mq =
  > strip =
  > mqext = $TESTDIR/hgext/mqext
  > EOF

  $ hg init server
  $ cd server
  $ touch foo
  $ hg -q commit -A -m initial
  $ cd ..

Clone does a pull but doesn't have MQ patches applied, so it should work

  $ hg -q clone --pull server client
  $ cd server
  $ touch bar
  $ hg -q commit -A -m second
  $ cd ..

Pull should not be allowed if MQ patches applied.

  $ cd client

  $ echo 1 > foo
  $ hg qnew patch1
  $ hg pull
  pulling from $TESTTMP/server
  searching for changes
  cannot pull with MQ patches applied
  (allow this behavior by setting mqext.allowexchangewithapplied=true)
  abort: prechangegroup.mqpreventpull hook failed
  [255]

Default behavior can be changed via config option.

  $ hg --config mqext.allowexchangewithapplied=true pull
  pulling from $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)

Strip operations are allowed (because they aren't push or pull)

  $ echo 2 > foo
  $ hg qnew patch2

  $ hg log -G -T '{node|short} {desc}\n'
  @  * [mq]: patch2 (glob)
  |
  | o  7d048dab3be9 second
  | |
  o |  * [mq]: patch1 (glob)
  |/
  o  96ee1d7354c4 initial
  

  $ hg strip -r 7d048dab3be9
  saved backup bundle to $TESTTMP/client/.hg/strip-backup/7d048dab3be9-c9c25be3-backup.hg (glob)
