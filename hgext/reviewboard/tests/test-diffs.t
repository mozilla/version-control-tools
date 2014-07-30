  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

Set up the repo

  $ cd client
  $ echo 'foo' > foo
  $ echo 'bar' > bar
  $ hg commit -A -m 'root commit'
  adding bar
  adding foo
  $ hg push --noreview
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 2 changes to 2 files
  $ hg phase --public -r .

Push a single commit

  $ echo 'updated foo' > foo
  $ hg commit -m 'Bug 300124 - Updated foo component'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  submitting 1 changesets for review
  
  changeset:  1:8078da8bec9f
  summary:    Bug 300124 - Updated foo component
  review:     http://localhost:$HGPORT1/r/2 (pending)
  
  review id:  bz://300124/mynick
  review url: http://localhost:$HGPORT1/r/1 (pending)

  $ rbmanage ../rbserver dumpreview $HGPORT1 1
  Review: 1
    Status: pending
    Commit ID: bz://300124/mynick
    Extra:
      p2rb: True
      p2rb.commits: [["8078da8bec9fca76a56ce358bb0addd12c83e708", "2"]]
      p2rb.identifier: bz://300124/mynick
      p2rb.is_squashed: True
  Draft: 1
    Commit ID: bz://300124/mynick
    Summary: Review for review ID: bz://300124/mynick
    Description:
      /r/2 - Bug 300124 - Updated foo component
      
      Pull down this commit:
      
      hg pull review -r 8078da8bec9fca76a56ce358bb0addd12c83e708
      
    Extra:
      p2rb: True
      p2rb.identifier: bz://300124/mynick
      p2rb.is_squashed: True
  Diff: 1
    Revision: 1
  diff -r 969306ef77c5 -r 8078da8bec9f foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo
  +updated foo
  

  $ rbmanage ../rbserver dumpreview $HGPORT1 2
  Review: 2
    Status: pending
    Commit ID: 8078da8bec9fca76a56ce358bb0addd12c83e708
    Extra:
      p2rb: True
      p2rb.identifier: bz://300124/mynick
      p2rb.is_squashed: False
  Draft: 2
    Commit ID: 8078da8bec9fca76a56ce358bb0addd12c83e708
    Summary: Bug 300124 - Updated foo component
    Description:
      Bug 300124 - Updated foo component
    Extra:
      p2rb: True
      p2rb.identifier: bz://300124/mynick
      p2rb.is_squashed: False
  Diff: 2
    Revision: 1
  diff -r 969306ef77c5 -r 8078da8bec9f foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -foo
  +updated foo
  

  $ hg phase --public -r .

Pushing multiple commits should result in parent diffs

  $ echo 'updated bar' > bar
  $ hg commit -m 'Bug 10000 - updated bar'
  $ echo 'updated foo again' > foo
  $ hg commit -m 'updated foo again'
  $ echo 'updated bar again' > bar
  $ hg commit -m 'updated bar again'
  $ hg push
  pushing to ssh://user@dummy/$TESTTMP/server
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 2 files
  submitting 3 changesets for review
  
  changeset:  2:393666323ae9
  summary:    Bug 10000 - updated bar
  review:     http://localhost:$HGPORT1/r/4 (pending)
  
  changeset:  3:5638d29dda51
  summary:    updated foo again
  review:     http://localhost:$HGPORT1/r/5 (pending)
  
  changeset:  4:c5acb46cb0f7
  summary:    updated bar again
  review:     http://localhost:$HGPORT1/r/6 (pending)
  
  review id:  bz://10000/mynick
  review url: http://localhost:$HGPORT1/r/3 (pending)

  $ rbmanage ../rbserver dumpreview $HGPORT1 3
  Review: 3
    Status: pending
    Commit ID: bz://10000/mynick
    Extra:
      p2rb: True
      p2rb.commits: [["393666323ae92d185152eaa15bda086f01f2b115", "4"], ["5638d29dda5131a2a79bf6ac7c465dd3a7052275", "5"], ["c5acb46cb0f75caf1566a2af32fad101798f1178", "6"]]
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: True
  Draft: 3
    Commit ID: bz://10000/mynick
    Summary: Review for review ID: bz://10000/mynick
    Description:
      /r/4 - Bug 10000 - updated bar
      /r/5 - updated foo again
      /r/6 - updated bar again
      
      Pull down these commits:
      
      hg pull review -r c5acb46cb0f75caf1566a2af32fad101798f1178
      
    Extra:
      p2rb: True
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: True
  Diff: 3
    Revision: 1
  diff -r 8078da8bec9f -r c5acb46cb0f7 bar
  --- a/bar	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -bar
  +updated bar again
  diff -r 8078da8bec9f -r c5acb46cb0f7 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -updated foo
  +updated foo again
  
  $ rbmanage ../rbserver dumpreview $HGPORT1 4
  Review: 4
    Status: pending
    Commit ID: 393666323ae92d185152eaa15bda086f01f2b115
    Extra:
      p2rb: True
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: False
  Draft: 4
    Commit ID: 393666323ae92d185152eaa15bda086f01f2b115
    Summary: Bug 10000 - updated bar
    Description:
      Bug 10000 - updated bar
    Extra:
      p2rb: True
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: False
  Diff: 4
    Revision: 1
  diff -r 8078da8bec9f -r 393666323ae9 bar
  --- a/bar	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -bar
  +updated bar
  

  $ rbmanage ../rbserver dumpreview $HGPORT1 5
  Review: 5
    Status: pending
    Commit ID: 5638d29dda5131a2a79bf6ac7c465dd3a7052275
    Extra:
      p2rb: True
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: False
  Draft: 5
    Commit ID: 5638d29dda5131a2a79bf6ac7c465dd3a7052275
    Summary: updated foo again
    Description:
      updated foo again
    Extra:
      p2rb: True
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: False
  Diff: 5
    Revision: 1
  diff -r 393666323ae9 -r 5638d29dda51 foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -updated foo
  +updated foo again
  

  $ rbmanage ../rbserver dumpreview $HGPORT1 6
  Review: 6
    Status: pending
    Commit ID: c5acb46cb0f75caf1566a2af32fad101798f1178
    Extra:
      p2rb: True
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: False
  Draft: 6
    Commit ID: c5acb46cb0f75caf1566a2af32fad101798f1178
    Summary: updated bar again
    Description:
      updated bar again
    Extra:
      p2rb: True
      p2rb.identifier: bz://10000/mynick
      p2rb.is_squashed: False
  Diff: 6
    Revision: 1
  diff -r 5638d29dda51 -r c5acb46cb0f7 bar
  --- a/bar	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -updated bar
  +updated bar again
  
