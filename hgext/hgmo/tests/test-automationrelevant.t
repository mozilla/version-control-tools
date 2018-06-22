  $ export USER=testuser
  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ echo p1_1 > foo
  $ hg commit -m 'push 1 commit 1'
  $ echo p1_2 > foo
  $ hg commit -m 'push 1 commit 2'
  $ hg -q push

  $ echo p2_1 > foo
  $ hg commit -m 'push 2 commit 1'
  $ echo p2_2 > foo
  $ hg commit -m 'push 2 commit 2'
  $ echo p2_3 > foo
  $ hg commit -m 'push 2 commit 3'
  $ hg -q push

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF

  $ cd ../server

Querying the tip of a push should return all changesets in the push

  $ hg log -r 'automationrelevant(2)' -T '{rev} {desc}\n'
  1 push 1 commit 1
  2 push 1 commit 2

  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Middle of a push should return ancestor changesets in the push

  $ hg log -r 'automationrelevant(4)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2

Bottom of a push should return just that changeset

  $ hg log -r 'automationrelevant(1)' -T '{rev} {desc}\n'
  1 push 1 commit 1

  $ hg log -r 'automationrelevant(3)' -T '{rev} {desc}\n'
  3 push 2 commit 1

Now move some phases to draft to verify draft changesets spanning pushes are included

Tip to draft should still return entire push

  $ hg phase -f --draft -r 5
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Tip ancestor to draft should still return entire push

  $ hg phase -f --draft -r 4
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Push base to draft should still return entire push

  $ hg phase -f --draft -r 3
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

  $ hg log -r 'automationrelevant(4)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2

Draft from previous push head not included unless config option changes behavior

  $ hg phase -f --draft -r 2

  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

  $ hg --config hgmo.automationrelevantdraftancestors=true log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  2 push 1 commit 2
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Draft from previous push base not included unless config option changes behavior

  $ hg phase -f --draft -r 1

  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

  $ hg --config hgmo.automationrelevantdraftancestors=true log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  1 push 1 commit 1
  2 push 1 commit 2
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

web command for exposing automation relevance works

  $ http http://localhost:$HGPORT/json-automationrelevance/tip --header content-type
  200
  content-type: application/json
  
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
        "desc": "push 2 commit 1",
        "extra": {
          "branch": "default"
        },
        "files": [
          "foo"
        ],
        "node": "13855aae8fb3291c663ff46a8510c0e3fa673a4c",
        "parents": [
          "cb5c79007e91b09a4ba7ebe9210311491d09e96e"
        ],
        "pushdate": [
          \d+, (re)
          0
        ],
        "pushhead": "5d04c4fd236c19e241d1587e120b39840344eee8",
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
        "desc": "push 2 commit 2",
        "extra": {
          "branch": "default"
        },
        "files": [
          "foo"
        ],
        "node": "66a66c6c6ae312ec88240754300468a6cea8f71d",
        "parents": [
          "13855aae8fb3291c663ff46a8510c0e3fa673a4c"
        ],
        "pushdate": [
          \d+, (re)
          0
        ],
        "pushhead": "5d04c4fd236c19e241d1587e120b39840344eee8",
        "pushid": 3,
        "pushuser": "testuser",
        "rev": 4,
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
        "desc": "push 2 commit 3",
        "extra": {
          "branch": "default"
        },
        "files": [
          "foo"
        ],
        "node": "5d04c4fd236c19e241d1587e120b39840344eee8",
        "parents": [
          "66a66c6c6ae312ec88240754300468a6cea8f71d"
        ],
        "pushdate": [
          \d+, (re)
          0
        ],
        "pushhead": "5d04c4fd236c19e241d1587e120b39840344eee8",
        "pushid": 3,
        "pushuser": "testuser",
        "rev": 5,
        "reviewers": []
      }
    ],
    "visible": true
  }


Confirm no errors in log

  $ cat error.log
