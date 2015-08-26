  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

Initialize a repo and turn off mq.

  $ mkdir repo
  $ cd repo
  $ hg init
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > mq = !
  > [experimental]
  > evolution = all
  > EOF

Construct an obsolescence graph

  $ touch file.txt
  $ hg add file.txt
  $ hg commit -m init
  $ hg book init
  $ init=$(hg log -r init -T '{node}')
  $ for n in orig base split1 split2 join; do
  >   hg up -r 0
  >   echo $n > file.txt
  >   hg commit -m patch-$n
  >   hg book $n
  >   eval $n=$(hg log -r $n -T '{node}')
  > done
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark init)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark orig)
  created new head
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark base)
  created new head
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark split1)
  created new head
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (leaving bookmark split2)
  created new head
  $ hg debugobsolete $orig $base
  $ hg debugobsolete $base $split1 $split2
  $ hg debugobsolete $split1 $join
  $ hg debugobsolete $split2 $join
  $ hg id -r "basechange(init)"
  63f3804db80c init
  $ cat << EOF | while read rev expect expect_name; do hg log --hidden -r "basechange($rev)" -T "base of $rev is {bookmarks}\n"; done
  > init $init init
  > base $base base
  > split1 $base base
  > split2 $split2 split2
  > join $base base
  > EOF
  base of init is init
  base of base is orig
  base of split1 is orig
  base of split2 is split2
  base of join is orig
