#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardgitrepo grepo > /dev/null 2>&1

--move-to-subdir will move files in git repo to subdirectory in hg

  $ linearize-git-to-hg --move-to-subdir subdir file://$TESTTMP/grepo master grepo-source grepo-dest-0 > /dev/null 2>&1

  $ hg --cwd grepo-dest-0 files -r tip
  subdir/bar
  subdir/file0-copied-with-move
  subdir/file0-copy0
  subdir/file0-copy1
  subdir/file0-copy2
  subdir/file0-moved-with-copy
  subdir/file1
  subdir/file1-20
  subdir/file1-50
  subdir/file1-80
  subdir/foo

Multiple child directories works

  $ linearize-git-to-hg --move-to-subdir dir0/dir1/dir2 file://$TESTTMP/grepo master grepo-source grepo-dest-1 > /dev/null 2>&1

  $ hg --cwd grepo-dest-1 files -r tip
  dir0/dir1/dir2/bar
  dir0/dir1/dir2/file0-copied-with-move
  dir0/dir1/dir2/file0-copy0
  dir0/dir1/dir2/file0-copy1
  dir0/dir1/dir2/file0-copy2
  dir0/dir1/dir2/file0-moved-with-copy
  dir0/dir1/dir2/file1
  dir0/dir1/dir2/file1-20
  dir0/dir1/dir2/file1-50
  dir0/dir1/dir2/file1-80
  dir0/dir1/dir2/foo
