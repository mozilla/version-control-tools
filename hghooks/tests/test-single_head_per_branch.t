  $ hg init mozilla-central
  $ cat >> mozilla-central/.hg/hgrc << EOF
  > [hooks]
  > pretxnchangegroup.b_singlehead = python:mozhghooks.single_head_per_branch.hook
  > EOF

  $ cd mozilla-central
  $ echo orig > file.txt
  $ hg -q commit -A -m 'original commit'
  $ cd ..

  $ hg init client
  $ cd client
  $ hg -q pull -u ../mozilla-central

Pushing a head forward is allowed

  $ echo 'new text in orig repo' > file.txt
  $ hg commit -m 'second commit in mc'
  $ hg push ../mozilla-central
  pushing to ../mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Creating a new head on the default branch is not allowed

  $ hg -q up -r 0
  $ echo different > file.txt
  $ hg commit -m 'different commit'
  created new head
  $ hg push -f ../mozilla-central
  pushing to ../mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  
  
  ************************** ERROR ****************************
  Multiple heads detected on branch 'default'
  Only one head per branch is allowed!
  *************************************************************
  
  
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.b_singlehead hook failed
  [255]

Merging the two heads and pushing is allowed

  $ hg merge --tool internal:other -r 1
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg commit -m Merge

  $ hg push ../mozilla-central
  pushing to ../mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files

  $ cd ..

A closed branch head shouldn't impact things

  $ cd mozilla-central
  $ hg -q up -r tip^
  $ echo 'will close' > file.txt
  $ hg commit -m 'creating new head on default'
  created new head
  $ hg commit --close-branch -m 'closing old default branch'

  $ cd ../client
  $ hg -q pull ../mozilla-central

  $ echo 'after closed branch' > file.txt
  $ hg commit -m 'after closed branch'
  $ hg push ../mozilla-central
  pushing to ../mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

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

Hidden changesets should not impact head detection.

  $ cd ../mozilla-central
  $ cat >> .hg/hgrc << EOF
  > [experimental]
  > evolution.createmarkers = true
  > EOF

  $ hg up default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo hidden1 > file.txt
  $ hg commit -m 'hidden head 1'
  $ hg up .^
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo hidden2 > file.txt
  $ hg commit -m 'hidden head 2'
  created new head
  $ hg debugobsolete 0e85a332921b9487fc3b6b033653d9b250b1716c
  1 new obsolescence markers
  obsoleted 1 changesets
  $ hg debugobsolete befc484a90fb5120f14f15a65e24e1b84e773e76
  1 new obsolescence markers
  obsoleted 1 changesets

  $ cd ..

  $ hg clone --pull mozilla-central client3
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 9 changesets with 8 changes to 1 files (+1 heads)
  new changesets c234df62ae3d:befc484a90fb (?)
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd client3
  $ echo non-hidden > file.txt
  $ hg commit -m 'commit after hidden'
  $ hg push -f
  pushing to $TESTTMP/mozilla-central
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ cd ..
