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

  $ cat > mach << EOF
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
  @  changeset:   3:059cd3ee4b4d
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   2:0088d44a4e42
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   1:a23f48517f2e
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add bar.cpp before the hook is set
  |
  o  changeset:   0:7ee4c4e22a8d
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add mach
  
  $ hg rebase -s 2 -d 0
  rebasing 2:0088d44a4e42 "second commit"
  rebasing 3:059cd3ee4b4d "third commit" (tip)
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/0088d44a4e42-bbfa5a85-rebase.hg
  $ hg export -r 1 | grep -v -q "int clang_format=42"
  $ hg export -r 2 | grep -q "int clang_format=42"
  $ hg export -r 3 | grep -q "int clang_format=42"

Update (should not run the hook)

  $ hg update -r 2
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg export -r 1 | grep -v -q "int clang_format=42"
  $ hg export -r 2 | grep -q "int clang_format=42"
  $ hg rebase -s 1 -d 3
  rebasing 1:a23f48517f2e "Add bar.cpp before the hook is set"
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/a23f48517f2e-a25c03d1-rebase.hg
  $ hg update -r tip
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

Histedit

  $ echo "histedit =" >> $HGRCPATH
  $ cat > histeditcommands << EOF
  > mess 866d807fd982 3
  > pick fdf8beeead16 2
  > pick 7ee4c4e22a8d 0
  > pick bc49f9b033d1 1
  > EOF
  $ hg histedit --commands histeditcommands
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/7ee4c4e22a8d-1462040c-histedit.hg
  $ hg log --graph
  @  changeset:   3:72c566e9cf17
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   2:cfc3e492707a
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add mach
  |
  o  changeset:   1:77a3ec17cbe9
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   0:3e55a2746795
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add bar.cpp before the hook is set
  
  $ hg export -r 0 | grep -v -q "int clang_format=42"

Check that histedit didn't run mach again

  $ hg export -r 3|grep -c 'int clang_format=42'
  1

Make a change and amend, confirming mach ran

  $ cat > asdf.cpp << EOF
  > int foo(int a) { printf("bar\n"); }
  > EOF
  $ hg add asdf.cpp
  $ hg commit -m "Initial commit for asdf.cpp"
  Reformatting 'asdf.cpp'
  $ echo "int a=2;" >> asdf.cpp
  $ hg -q commit --amend asdf.cpp
  Reformatting 'asdf.cpp'
  $ cat asdf.cpp
  int foo(int a) { printf("bar\n"); }
  int clang_format=42;
  int a=2;
  int clang_format=42;
