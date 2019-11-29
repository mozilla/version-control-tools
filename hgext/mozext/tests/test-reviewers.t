  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > mozext = $TESTDIR/hgext/mozext
  > EOF

  $ hg init repo
  $ cd repo
  $ echo line > file1.txt
  $ hg add file1.txt
  $ hg commit -m "no bug: r=user1"
  $ echo line > file2.txt
  $ hg add file2.txt
  $ hg commit -m "no bug: r=user2"

Check reviewer using uncommitted diff

  $ echo "other line" > file1.txt
  $ hg reviewers
  Potential reviewers:
    1. user1
  
  $ hg up --clean -q

Check reviewer using last revision

  $ echo "other line" > file2.txt
  $ hg commit -m "no bug: r=user3"
  $ hg reviewers
  Potential reviewers:
    1. user3
    2. user2
  
