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
  > import sys
  > filename = sys.argv[-1]
  > print("Reformatting '%s'" % filename)
  > with open(filename, 'a') as f:
  >     f.write('int clang_format=42;\n')
  > 
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
  $ python mach clang-format -p foo.cpp
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
  @  changeset:   3:423309da9f44
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   2:94f859340388
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   1:ba0c923d4430
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add bar.cpp before the hook is set
  |
  o  changeset:   0:e9bf9f146b90
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add mach
  
  $ hg rebase -s 2 -d 0
  rebasing 2:94f859340388 "second commit"
  rebasing 3:423309da9f44 tip "third commit" (hg59 !)
  rebasing 3:423309da9f44 "third commit" (tip) (no-hg59 !)
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/94f859340388-a6dc420b-rebase.hg
  $ hg export -r 1 | grep -v -q "int clang_format=42"
  $ hg export -r 2 | grep -q "int clang_format=42"
  $ hg export -r 3 | grep -q "int clang_format=42"

Update (should not run the hook)

  $ hg update -r 2
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg export -r 1 | grep -v -q "int clang_format=42"
  $ hg export -r 2 | grep -q "int clang_format=42"
  $ hg rebase -s 1 -d 3
  rebasing 1:ba0c923d4430 "Add bar.cpp before the hook is set"
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/ba0c923d4430-cefd6852-rebase.hg
  $ hg update -r tip
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

Histedit

  $ echo "histedit =" >> $HGRCPATH
  $ cat > histeditcommands << EOF
  > mess ba4e12a3249d 3
  > pick 7f98a115cbbc 2
  > pick e9bf9f146b90 0
  > pick e1bd65ca6d5f 1
  > EOF
  $ hg histedit --commands histeditcommands
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/e9bf9f146b90-3976ffbc-histedit.hg
  $ hg log --graph
  @  changeset:   3:44ee0173f95e
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   2:36d2eb569efd
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add mach
  |
  o  changeset:   1:6f3da0e785ee
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   0:5c9f66f821de
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

Confirm hook doesn't run when `MOZPHAB` environment variable is set

  $ cat << EOF > no-hook.cpp
  > int foo(int a) { printf("bar\n"); }
  > EOF
  $ hg add no-hook.cpp
  $ MOZPHAB=1 hg commit -m "no reformat"
  $ grep -q "int clang_format=42" no-hook.cpp
  [1]

Ensure hook doesn't interact with non-Firefox repos

  $ cd ..
  $ mkdir non-ff
  $ cd non-ff
  $ hg init
  $ echo foo > bar
  $ hg commit -A -m initial
  adding bar
