Create the testing repo

  $ . $TESTDIR/testing/firefoxrepos.sh
  $ makefirefoxreposserver root $HGPORT
  $ installfakereposerver $HGPORT
  $ populatedummydata root > /dev/null

  $ hg init repo1
  $ cd repo1
  $ touch .hg/IS_FIREFOX_REPO

Create the fake mach
It will take the file and add something at the end of the file


  $ cat << EOF > mach
  > #!/bin/sh
  > filename=\$3
  > echo "Reformatting '\$filename'"
  > echo 'int clang_format=42;' >> \$filename
  > EOF
  $ chmod +x mach
  $ hg add mach
  $ hg commit --message 'Add mach' mach
  $ mkdir dir-0
  $ cat << EOF > dir-0/bar.cpp
  > int foo(int a) { printf("bar\n"); }
  > EOF
  $ hg add dir-0/bar.cpp
  $ hg commit --message 'Add bar.cpp before the hook is set'
  $ hg export -r 1|grep -v -q "int clang_format=42"

Configure the hook

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > clang-format = $TESTDIR/hgext/clang-format
  > rebase =
  > EOF

Test the clang-format hook

  $ touch foo.cpp
  $ ./mach clang-format -p foo.cpp
  Reformatting 'foo.cpp'
  $ grep -q "int clang_format=42" foo.cpp
  $ rm foo.cpp

Commit a file and check that the hook did the right job

  $ mkdir dir-1
  $ cat << EOF > dir-1/bar.cpp
  > int foo(int a) { printf("bar\n"); }
  > EOF
  $ hg add .
  adding dir-1/bar.cpp
  $ hg commit --message 'second commit'
  Reformatting 'dir-1/bar.cpp'
  $ grep -q "int clang_format=42" dir-1/bar.cpp

Rebase (should not run the hook)

  $ mkdir dir-2
  $ cat << EOF > dir-2/bar.cpp
  > int foo2(int a) { printf("bar\n"); }
  > EOF
  $ hg add .
  adding dir-2/bar.cpp
  $ hg commit --message 'third commit'
  Reformatting 'dir-2/bar.cpp'
  $ grep -q "int clang_format=42" dir-2/bar.cpp
  $ hg log --graph
  @  changeset:   3:b0fbd9def0e3
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   2:95690b3319a1
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   1:1d54f3d82651
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add bar.cpp before the hook is set
  |
  o  changeset:   0:a3a45b056201
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add mach
  
  $ hg rebase -s 2 -d 0
  rebasing 2:95690b3319a1 "second commit"
  rebasing 3:b0fbd9def0e3 "third commit" (tip)
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/95690b3319a1-5827bfda-rebase.hg
  $ hg export -r 1|grep -v -q "int clang_format=42"
  $ hg export -r 2|grep -q "int clang_format=42"
  $ hg export -r 3|grep -q "int clang_format=42"

Update (should not run the hook)

  $ hg update -r 2
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg export -r 1|grep -v -q "int clang_format=42"
  $ hg export -r 2|grep -q "int clang_format=42"
  $ hg rebase -s 1 -d 3
  rebasing 1:1d54f3d82651 "Add bar.cpp before the hook is set"
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/1d54f3d82651-d3024fe4-rebase.hg
  $ hg update -r tip
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

Histedit
  $ echo "histedit =" >> $HGRCPATH
  $ hg histedit --commands - 2>&1 << EOF
  > mess c53048a4bfcd a
  > pick a96e0d222810 c
  > pick a3a45b056201 f
  > pick 8cf6684113a7 d
  > EOF
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/a3a45b056201-11e8b9e2-histedit.hg
  $ hg log --graph
  @  changeset:   3:a0090a232748
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   2:205cd4d3abf5
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add mach
  |
  o  changeset:   1:3dd5a8ab22d3
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   0:805d736bb819
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add bar.cpp before the hook is set
  
  $ hg export -r 0|grep -v -q "int clang_format=42"
Check that histedit didn't run mach again
  $ test $(hg export -r 3|grep -c 'int clang_format=42') -eq 1
