  $ . $TESTDIR/hghooks/tests/common.sh
  $ hg init server
  $ configurehooks server
  $ cd server
  $ echo orig > file.txt
  $ hg -q commit -A -m 'original commit'
  $ cd ..

  $ hg init client
  $ cd client
  $ hg -q pull -u ../server

Pushing a head forward is allowed

  $ echo 'new text in orig repo' > file.txt
  $ hg commit -m 'second commit on default'
  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Creating a new branch is allowed

  $ hg -q up -r 0
  $ echo different > file.txt
  $ hg branch branch
  marked working directory as branch branch
  (branches are permanent and global, did you want a bookmark?)
  $ hg commit -m 'different commit'
  $ hg push --new-branch ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)

Merging the two heads and pushing is allowed

  $ hg merge --tool internal:other -r 1
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  (branch merge, don?t forget to commit) (glob)
  $ hg commit -m Merge


  $ hg push ../server
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (-1 heads)

Pushing to two branches at the same time is not allowed

  $ echo branch > file.txt
  $ hg commit -m 'update branch'
  $ hg up default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo default > file.txt
  $ hg commit -m 'update default'
  $ hg push ../server  
  pushing to ../server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  *** pushing multiple branches ***
  
  This push includes changesets in several branches: branch, default
  
  Your push is being rejected because this is almost certainly not what you
  intended.
  transaction abort!
  rollback completed
  abort: pretxnchangegroup.mozhooks hook failed
  [255]
