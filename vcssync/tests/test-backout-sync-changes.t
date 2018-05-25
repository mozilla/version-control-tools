  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ mkdir -p src/sub
  $ echo new >src/one
  $ echo new >src/two
  $ echo new >src/sub/three
  $ mkdir dst
  $ echo old >dst/one

  $ find dst -type f | sort
  dst/one

new file, modified file

  $ test-apply-changes src dst one,two
  updating dst/one
  creating dst/two
  $ find dst -type f | sort
  dst/one
  dst/two
  $ cat dst/one
  new

subdir

  $ test-apply-changes src dst sub/three
  creating dst/sub/three
  $ find dst -type f | sort
  dst/one
  dst/sub/three
  dst/two
  $ cat dst/sub/three
  new

renamed file

  $ mv src/one src/four
  $ test-apply-changes src dst one,four
  deleting dst/one
  creating dst/four
  $ find dst -type f | sort
  dst/four
  dst/sub/three
  dst/two

renamed subdir

  $ mv src/sub src/def
  $ test-apply-changes src dst sub/three,def/three
  deleting dst/sub/three
  deleting dst/sub/
  creating dst/def/three
  $ find dst -type f | sort
  dst/def/three
  dst/four
  dst/two

deleted file

  $ rm src/two
  $ test-apply-changes src dst two
  deleting dst/two
  $ find dst -type f | sort
  dst/def/three
  dst/four

deleted subdir

  $ rm src/def/three; rmdir src/def
  $ test-apply-changes src dst def/three
  deleting dst/def/three
  deleting dst/def/
  $ find dst -type f | sort
  dst/four

