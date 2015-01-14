  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > qbackout = $TESTDIR/hgext/qbackout
  > EOF

  $ hg init repo
  $ cd repo
  $ echo line1 > file1.txt
  $ echo line1 > file2.txt
  $ hg add file1.txt file2.txt
  $ hg commit -m initial -u author1 # rev 0
  $ echo line2 >> file1.txt
  $ hg commit -m 'commit 2' -u author2 # rev 1
  $ echo line2 >> file2.txt
  $ hg commit -m 'commit 3' -u author3 # rev 2

Single-commit backout:

  $ hg oops -r 1
  checking for uncommitted changes
  backing out 22355b867c01
  applying patch from stdin
  $ hg log -r . --template '{desc}\n'
  Backed out changeset 22355b867c01

Reapply single-commit backout:

  $ hg oops -r 1 --apply
  checking for uncommitted changes
  Reapplying 22355b867c01
  applying patch from stdin
  $ hg log -r . --template '{desc}\n'
  commit 2

Multi-commit backout:

  $ hg oops -r 1:2
  checking for uncommitted changes
  backing out 5b367719b421
  applying patch from stdin
  backing out 22355b867c01
  applying patch from stdin
  $ hg log --template '{desc}\n' --limit 2
  Backed out changeset 22355b867c01
  Backed out changeset 5b367719b421

Reapply buried backout:

  $ hg oops --apply -r 1
  checking for uncommitted changes
  Reapplying 22355b867c01
  applying patch from stdin

Get back to original state:

  $ hg oops --apply -r 2
  checking for uncommitted changes
  Reapplying 5b367719b421
  applying patch from stdin

Folding together multiple commits into a single backout changeset:

  $ hg oops -r 1:2 -s
  checking for uncommitted changes
  backing out 5b367719b421
  applying patch from stdin
  backing out 22355b867c01
  applying patch from stdin
  $ hg log --template '{desc}\n' -r .
  Backed out 2 changesets
  
  Backed out changeset 5b367719b421
  Backed out changeset 22355b867c01

Backouts should be 'test' user, re-applies should be original user:

  $ hg log --template '<{author}> {desc|firstline}\n'
  <test> Backed out 2 changesets
  <author3> commit 3
  <author2> commit 2
  <test> Backed out changeset 22355b867c01
  <test> Backed out changeset 5b367719b421
  <author2> commit 2
  <test> Backed out changeset 22355b867c01
  <author3> commit 3
  <author2> commit 2
  <author1> initial

Clean up

  $ hg oops --apply -r 1+2
  checking for uncommitted changes
  Reapplying 22355b867c01
  applying patch from stdin
  Reapplying 5b367719b421
  applying patch from stdin

Patches should be automatically sorted into correct order:

  $ hg oops -r 1+2
  checking for uncommitted changes
  backing out 5b367719b421
  applying patch from stdin
  backing out 22355b867c01
  applying patch from stdin
  $ hg log --template '{desc}\n' --limit 2
  Backed out changeset 22355b867c01
  Backed out changeset 5b367719b421
  $ hg oops --apply -r 1+2
  checking for uncommitted changes
  Reapplying 22355b867c01
  applying patch from stdin
  Reapplying 5b367719b421
  applying patch from stdin
  $ hg oops -r 2+1
  checking for uncommitted changes
  backing out 5b367719b421
  applying patch from stdin
  backing out 22355b867c01
  applying patch from stdin
  $ hg log --template '{desc}\n' --limit 2
  Backed out changeset 22355b867c01
  Backed out changeset 5b367719b421
  $ hg oops --apply -r 1+2
  checking for uncommitted changes
  Reapplying 22355b867c01
  applying patch from stdin
  Reapplying 5b367719b421
  applying patch from stdin

Some error cases

  $ hg oops
  checking for uncommitted changes
  abort: at least one revision required
  [255]
  $ hg oops -s
  checking for uncommitted changes
  abort: at least one revision required
  [255]
  $ hg oops --nopush -r 1 2>&1 | head -1
  hg oops: option --nopush not recognized
