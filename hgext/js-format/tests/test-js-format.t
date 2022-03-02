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
  >     f.write('let js_format=42;\n')
  > 
  > EOF
  $ chmod +x mach
  $ hg add mach
  $ hg commit --message 'Add mach' mach
  $ mkdir dir-0
  $ cat << EOF > dir-0/bar.js
  > function foo(a) { console.log("bar\n"); }
  > EOF
  $ hg add dir-0/bar.js
  $ hg commit --message 'Add bar.js before the hook is set'
  $ hg export -r 1|grep -v -q "let js_format=42"

Configure the hook

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > js-format = $TESTDIR/hgext/js-format
  > rebase =
  > EOF

Test the js-format hook

  $ touch foo.js
  $ python mach eslint --fix foo.js
  Reformatting 'foo.js'
  $ grep -q "let js_format=42" foo.js
  $ rm foo.js

Commit a file and check that the hook did the right job

  $ mkdir dir-1
  $ cat << EOF > dir-1/bar.js
  > function foo(a) { console.log("bar\n"); }
  > EOF
  $ hg add .
  adding dir-1/bar.js
  $ hg commit --message 'second commit'
  Reformatting 'dir-1/bar.js'
  $ grep -q "let js_format=42" dir-1/bar.js

Rebase (should not run the hook)

  $ mkdir dir-2
  $ cat << EOF > dir-2/bar.js
  > function foo(a) { console.log("bar\n"); }
  > EOF
  $ hg add .
  adding dir-2/bar.js
  $ hg commit --message 'third commit'
  Reformatting 'dir-2/bar.js'
  $ grep -q "let js_format=42" dir-2/bar.js
  $ hg log --graph
  @  changeset:   3:90e129020fa7
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   2:9b431be05fe2
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   1:35241f108edc
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add bar.js before the hook is set
  |
  o  changeset:   0:6ba776e40796
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add mach
  
  $ hg rebase -s 2 -d 0
  rebasing 2:9b431be05fe2 "second commit"
  rebasing 3:90e129020fa7 tip "third commit" (hg59 !)
  rebasing 3:90e129020fa7 "third commit" (tip) (no-hg59 !)
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/9b431be05fe2-58db80a5-rebase.hg
  $ hg export -r 1 | grep -v -q "let js_format=42"
  $ hg export -r 2 | grep -q "let js_format=42"
  $ hg export -r 3 | grep -q "let js_format=42"

Update (should not run the hook)

  $ hg update -r 2
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg export -r 1 | grep -v -q "let js_format=42"
  $ hg export -r 2 | grep -q "let js_format=42"
  $ hg rebase -s 1 -d 3
  rebasing 1:35241f108edc "Add bar.js before the hook is set"
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/35241f108edc-93e75ffd-rebase.hg
  $ hg update -r tip
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

Histedit

  $ echo "histedit =" >> $HGRCPATH
  $ cat > histeditcommands << EOF
  > mess c0be2ad63b31 3
  > pick b4f546d348ab 2
  > pick 6ba776e40796 0
  > pick 47ccb8c84472 1
  > EOF
  $ hg histedit --commands histeditcommands
  saved backup bundle to $TESTTMP/repo1/.hg/strip-backup/6ba776e40796-62ae6ca4-histedit.hg
  $ hg log --graph
  @  changeset:   3:2fd8827288c4
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     second commit
  |
  o  changeset:   2:ee9d92c29808
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     Add mach
  |
  o  changeset:   1:fae7b6a64e0f
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     third commit
  |
  o  changeset:   0:a4f4d7995acf
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     Add bar.js before the hook is set
  
  $ hg export -r 0 | grep -v -q "let js_format=42"

Check that histedit didn't run mach again

  $ hg export -r 3|grep -c 'let js_format=42'
  1

Make a change and amend, confirming mach ran

  $ cat > asdf.js << EOF
  > function foo(a) { console.log("bar\n"); }
  > EOF
  $ hg add asdf.js
  $ hg commit -m "Initial commit for asdf.js"
  Reformatting 'asdf.js'
  $ echo "let a=2;" >> asdf.js
  $ hg -q commit --amend asdf.js
  Reformatting 'asdf.js'
  $ cat asdf.js
  function foo(a) { console.log("bar\n"); }
  let js_format=42;
  let a=2;
  let js_format=42;

Confirm hook doesn't run when `MOZPHAB` environment variable is set

  $ cat << EOF > no-hook.js
  > function foo(a) { console.log("bar\n"); }
  > EOF
  $ hg add no-hook.js
  $ MOZPHAB=1 hg commit -m "no reformat"
  $ grep -q "let js_format=42" no-hook.js
  [1]

Ensure hook doesn't interact with non-Firefox repos

  $ cd ..
  $ mkdir non-ff
  $ cd non-ff
  $ hg init
  $ echo foo > bar
  $ hg commit -A -m initial
  adding bar
