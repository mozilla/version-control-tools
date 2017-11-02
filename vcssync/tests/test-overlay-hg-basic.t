#require hg41

  $ . $TESTDIR/vcssync/tests/helpers.sh
  $ standardoverlayenv > /dev/null 2>&1

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   repo --into subdir
  repo does not exist; cloning http://localhost:$HGPORT/overlay-dest
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 2 changes to 2 files
  executing: hg strip --no-backup -r 'not public()'
  hg> abort: empty revision set
  (ignoring strip failure)
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> pulling http://localhost:$HGPORT/overlay-source into $TESTTMP/repo/.hg/localhost~3a*__overlay-source (glob)
  hg> requesting all changes
  hg> adding changesets
  hg> adding manifests
  hg> adding file changes
  hg> added 2 changesets with 3 changes to 3 files
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  $ cd repo

Overlayed changesets exist in proper location, have proper paths

  $ hg log -G --debug -p
  o  changeset:   2:eaf64eb119642ef85b4d952a49d0f5c815d5bcd1
  |  tag:         tip
  |  phase:       draft
  |  parent:      1:67c9543981c6d2001ab6f30dd7fbe83c3d55d33b
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    2:822b75cff23425e6d024bd2da11312cc68579a0c
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  files+:      subdir/dir0/file0
  |  extra:       branch=default
  |  extra:       subtree_revision=d92cc0ff6f1a1afa1d57e8c11c75874bbd991058
  |  extra:       subtree_source=http://example.com/dummy-overlay-source
  |  description:
  |  add dir0/file0
  |
  |
  |  diff -r 67c9543981c6d2001ab6f30dd7fbe83c3d55d33b -r eaf64eb119642ef85b4d952a49d0f5c815d5bcd1 subdir/dir0/file0
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/subdir/dir0/file0	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +1
  |
  o  changeset:   1:67c9543981c6d2001ab6f30dd7fbe83c3d55d33b
  |  phase:       draft
  |  parent:      0:88dd2a5005e6e795674d8253cec4dde9f9f77457
  |  parent:      -1:0000000000000000000000000000000000000000
  |  manifest:    1:4620d3269b1fa921c9e29f83c76ba5432642e86b
  |  user:        Test User <someone@example.com>
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  files+:      subdir/source-file0 subdir/source-file1
  |  extra:       branch=default
  |  extra:       subtree_revision=76f0fc85e215d86d04307b17c13356ad452d2297
  |  extra:       subtree_source=http://example.com/dummy-overlay-source
  |  description:
  |  initial - add source-file0 and source-file1
  |
  |
  |  diff -r 88dd2a5005e6e795674d8253cec4dde9f9f77457 -r 67c9543981c6d2001ab6f30dd7fbe83c3d55d33b subdir/source-file0
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/subdir/source-file0	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +source-file0
  |  diff -r 88dd2a5005e6e795674d8253cec4dde9f9f77457 -r 67c9543981c6d2001ab6f30dd7fbe83c3d55d33b subdir/source-file1
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/subdir/source-file1	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +source-file1
  |
  o  changeset:   0:88dd2a5005e6e795674d8253cec4dde9f9f77457
     phase:       public
     parent:      -1:0000000000000000000000000000000000000000
     parent:      -1:0000000000000000000000000000000000000000
     manifest:    0:03ae3abe8fc90de8aa92cb4fa79854b491a13045
     user:        Test User <someone@example.com>
     date:        Thu Jan 01 00:00:00 1970 +0000
     files+:      dest-file0 dest-file1
     extra:       branch=default
     description:
     initial in dest
  
  
  

Running again will strip overlayed changesets (they aren't public)

  $ overlay-hg-repos http://localhost:$HGPORT/overlay-source http://localhost:$HGPORT/overlay-dest \
  >   . --into subdir
  executing: hg strip --no-backup -r 'not public()'
  resolving destination revision: tip
  executing: hg identify http://localhost:$HGPORT/overlay-dest -r tip
  hg> 88dd2a5005e6
  commencing overlay of http://localhost:$HGPORT/overlay-source
  executing: hg overlay http://localhost:$HGPORT/overlay-source --into subdir -d 88dd2a5005e6e795674d8253cec4dde9f9f77457
  hg> 76f0fc85e215 -> 67c9543981c6: initial - add source-file0 and source-file1
  hg> d92cc0ff6f1a -> eaf64eb11964: add dir0/file0
  2 new changesets; new tip is eaf64eb119642ef85b4d952a49d0f5c815d5bcd1

  $ hg log -G -T '{node|short} {desc}'
  o  eaf64eb11964 add dir0/file0
  |
  o  67c9543981c6 initial - add source-file0 and source-file1
  |
  o  88dd2a5005e6 initial in dest
  

