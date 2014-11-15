  $ hg init mozilla-central
  $ cat >> mozilla-central/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.b_singlehead = python:mozhghooks.single_head_per_branch.hook
  > EOF

  $ cd mozilla-central
  $ echo orig > file.txt
  $ hg -q commit -A -m 'original commit'
  $ echo 'new text in orig repo' > file.txt
  $ hg commit -m 'second commit in mc'
  $ cd ..

  $ hg init client
  $ cd client
  $ hg -q pull -r 0 -u ../mozilla-central

  $ echo different > file.txt
  $ hg commit -m 'different commit'
  $ hg push -f ../mozilla-central
  pushing to ../mozilla-central
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

  $ cd ..

A repository with multiple branches can still push when this hook is active

  $ hg -q clone mozilla-central client2
  $ cd client2
  $ hg branch newbranch
  marked working directory as branch newbranch
  (branches are permanent and global, did you want a bookmark?)
  $ echo 'newcontent' > file.txt
  $ hg commit -m 'new content in a new branch'
  $ hg push --new-branch ../mozilla-central
  pushing to ../mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ cd ..
