  $ . $TESTDIR/vcssync/tests/helpers.sh

  $ mkdir -p src/sub
  $ echo new >src/one
  $ echo new >src/two
  $ echo new >src/sub/three
  $ mkdir dst
  $ echo old >dst/one

  $ ls -R dst
  one

new file, modified file

  $ test-apply-changes src dst one,two
  updating dst/one
  creating dst/two
  $ ls -R dst
  one
  two
  $ cat dst/one
  new

subdir

  $ test-apply-changes src dst sub/three
  creating dst/sub/three
  $ ls -R dst
  one
  sub
  two
  
  dst/sub:
  three
  $ cat dst/sub/three
  new

renamed file

  $ mv src/one src/four
  $ test-apply-changes src dst one,four
  deleting dst/one
  creating dst/four
  $ ls -R dst
  four
  sub
  two
  
  dst/sub:
  three

renamed subdir

  $ mv src/sub src/def
  $ test-apply-changes src dst sub/three,def/three
  deleting dst/sub/three
  deleting dst/sub/
  creating dst/def/three
  $ ls -R dst
  def
  four
  two
  
  dst/def:
  three

deleted file

  $ rm src/two
  $ test-apply-changes src dst two
  deleting dst/two
  $ ls -R dst
  def
  four
  
  dst/def:
  three

deleted subdir

  $ rm src/def/three; rmdir src/def
  $ test-apply-changes src dst def/three
  deleting dst/def/three
  deleting dst/def/
  $ ls -R dst
  four

