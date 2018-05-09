  $ export USER=testuser
  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ cat >> $HGRCPATH << EOF
  > [experimental]
  > evolution = all
  > [phases]
  > publish = false
  > [extensions]
  > rebase =
  > EOF
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ echo p1_1 > file0
  $ hg -q commit -A -m 'push 1 commit 1'
  $ echo p1_2 > file0
  $ hg commit -m 'push 1 commit 2'
  $ hg phase --public -r .
  $ hg -q push

Create some obsolete changesets

  $ echo file1_1 > file1
  $ hg -q commit -A -m 'file1 1'
  $ echo file1_2 > file1
  $ hg commit -m 'file1 2'
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 2 changes to 1 files
  remote: recorded push in pushlog

  $ hg rebase -s 11743f808184 -d 96ee1d7354c4
  rebasing 3:11743f808184 "file1 1"
  rebasing 4:3208166ea109 "file1 2" (tip)
  $ hg push -f
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 2 changesets with 0 changes to 1 files (+1 heads)
  remote: recorded push in pushlog
  remote: 2 new obsolescence markers
  remote: obsoleted 2 changesets (?)

  $ cd ../server

Local revset evaluation against hidden changeset renders hidden message

  $ hg log -r 'automationrelevant(3208166ea109)'
  abort: hidden revision '3208166ea109'! (no-hg45 !)
  abort: hidden revision '3208166ea109' was rewritten as: 22296b97e5de! (hg45 !)
  (use --hidden to access hidden revisions)
  [255]

Unless --hidden is used

  $ hg --hidden log -r 'automationrelevant(3208166ea109)'
  changeset:   4:3208166ea109
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    rewritten using rebase as 6:22296b97e5de (?)
  summary:     file1 2
  

  $ hg --hidden --config hgmo.automationrelevantdraftancestors=true log -r 'automationrelevant(3208166ea109)'
  changeset:   3:11743f808184
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    rewritten using rebase as 5:4449a0888729 (?)
  summary:     file1 1
  
  changeset:   4:3208166ea109
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  obsolete:    rewritten using rebase as 6:22296b97e5de (?)
  summary:     file1 2
  

  $ http http://localhost:$HGPORT/json-automationrelevance/3208166ea109 --no-headers
  200
  
  {
    "changesets": [
      {
        "author": "test",
        "backsoutnodes": [],
        "bugs": [],
        "date": [
          0.0,
          0
        ],
        "desc": "file1 1",
        "extra": {
          "branch": "default"
        },
        "files": [
          "file1"
        ],
        "node": "11743f8081842eb047711e85120177ed46be343e",
        "parents": [
          "d406a5ad38f255efb8657338e56a2bd6b8149cca"
        ],
        "pushdate": [
          \d+, (re)
          0
        ],
        "pushhead": "3208166ea10954e86c390c32fe6f7166f06161b2",
        "pushid": 3,
        "pushuser": "testuser",
        "rev": 3,
        "reviewers": []
      },
      {
        "author": "test",
        "backsoutnodes": [],
        "bugs": [],
        "date": [
          0.0,
          0
        ],
        "desc": "file1 2",
        "extra": {
          "branch": "default"
        },
        "files": [
          "file1"
        ],
        "node": "3208166ea10954e86c390c32fe6f7166f06161b2",
        "parents": [
          "11743f8081842eb047711e85120177ed46be343e"
        ],
        "pushdate": [
          \d+, (re)
          0
        ],
        "pushhead": "3208166ea10954e86c390c32fe6f7166f06161b2",
        "pushid": 3,
        "pushuser": "testuser",
        "rev": 4,
        "reviewers": []
      }
    ],
    "visible": false
  }

  $ cd ..
