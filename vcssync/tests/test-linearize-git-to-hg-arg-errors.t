#require hg40+

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardgitrepo grepo > /dev/null 2>&1

Git source URL does not exist

  $ linearize-git-to-hg file://$TESTTMP/does/not/exist master dummy dummy
  Initialized empty Git repository in $TESTTMP/dummy/
  fatal: '$TESTTMP/does/not/exist' does not appear to be a git repository
  fatal: Could not read from remote repository.
  
  Please make sure you have the correct access rights
  and the repository exists.
  [1]

Source ref does not exist

  $ linearize-git-to-hg file://$TESTTMP/grepo badref grepo-clone dummy
  Initialized empty Git repository in $TESTTMP/grepo-clone/
  fatal: Couldn't find remote ref heads/badref
  fatal: The remote end hung up unexpectedly
  [1]
