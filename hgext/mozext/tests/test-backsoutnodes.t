  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > mozext = $TESTDIR/hgext/mozext
  > commitextra = $TESTDIR/hgext/hgmo/tests/commitextra.py
  > EOF

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg -q commit -A -m initial
  $ for i in 1 2 3 4 5; do
  >   echo $i > foo
  >   hg commit -m "Bug $i - change $i" --extra git_commit=`printf '%040d' $i`
  > done
  $ echo 6 > foo
  $ hg commit -m "Change without git commit"

A revert of multiple commits returns all of them, in revision order

  $ echo revert > foo
  $ hg commit -m 'Revert "Bug 4 - change 4" for causing failures
  > 
  > This reverts commit 0000000000000000000000000000000000000004.
  > 
  > Revert "Bug 2 - change 2" for causing failures
  > 
  > This reverts commit 0000000000000000000000000000000000000002.'

  $ hg log -r 2+4 -T '{node|short}\n'
  54da7cc898d7
  b3021f10719a
  $ hg log -r 7 -T '{join(backsoutnodes, " ")}\n'
  54da7cc898d7 b3021f10719a

Only the `backoutsearchlimit` most recent ancestors (including the revert) are
searched

  $ hg log -r 7 -T '{join(backsoutnodes, " ")}\n' --config mozext.backoutsearchlimit=5
  b3021f10719a
  $ hg log -r 7 -T '{join(backsoutnodes, " ")}\n' --config mozext.backoutsearchlimit=6
  54da7cc898d7 b3021f10719a

Reverted commits which can't be found are ignored

  $ echo unknown > foo
  $ hg commit -m 'Revert "Bug 9 - unknown change"
  > 
  > This reverts commit 0000000000000000000000000000000000000009.
  > 
  > Revert "Bug 5 - change 5"
  > 
  > This reverts commit 0000000000000000000000000000000000000005.'
  $ hg log -r 5 -T '{node|short}\n'
  bc61c4c0c059
  $ hg log -r 8 -T '{join(backsoutnodes, " ")}\n'
  bc61c4c0c059

Commits which are not ancestors of the revert are not considered, even if they
are more recent

  $ hg -q up 1
  $ echo other > bar
  $ hg -q commit -A -m "Bug 10 - change 10" --extra git_commit=`printf '%040d' 10`
  $ hg -q up 8
  $ echo revert-other > foo
  $ hg commit -m 'Revert "Bug 10 - change 10"
  > 
  > This reverts commit 0000000000000000000000000000000000000010.'
  $ hg log -r 10 -T '{join(backsoutnodes, " ")}\n'
  

Once merged, they are found

  $ hg -q merge 9
  $ hg commit -m "Merge"
  $ echo revert-merged > foo
  $ hg commit -m 'Revert "Bug 10 - change 10"
  > 
  > This reverts commit 0000000000000000000000000000000000000010.'
  $ hg log -r 9 -T '{node|short}\n'
  a3aeb4328625
  $ hg log -r 12 -T '{join(backsoutnodes, " ")}\n'
  a3aeb4328625
