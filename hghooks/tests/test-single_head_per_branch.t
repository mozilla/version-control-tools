  $ hg init mozilla-central
  $ cat >> mozilla-central/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.b_singlehead = python:mozhghooks.single_head_per_branch.hook
  > EOF
  $ echo 'orig' > mozilla-central/file.txt
  $ hg commit -R mozilla-central -A -m 'original commit'
  adding file.txt
  $ hg clone mozilla-central client
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo 'new text in orig repo' > mozilla-central/file.txt
  $ hg commit -R mozilla-central -A -m 'second commit in mc'
  $ echo 'different' > client/file.txt
  $ hg commit -R client -A -m 'different commit'
  $ hg push -R client -f
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  
  
  ************************** ERROR ****************************
  Multiple heads detected on branch 'default'
  Only one head per branch is allowed!
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.b_singlehead hook failed
  [255]



A repository with multiple branches can still push when this hook is active

  $ hg clone mozilla-central client2
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg branch -R client2 newbranch
  marked working directory as branch newbranch
  (branches are permanent and global, did you want a bookmark?)
  $ echo 'newcontent' > client2/file.txt
  $ hg commit -R client2 -A -m 'new content in a new branch'
  $ hg push -R client2 --new-branch
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
