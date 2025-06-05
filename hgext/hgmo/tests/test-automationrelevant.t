  $ export USER=testuser
  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to http://$LOCALHOST:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > commitextra = $TESTDIR/hgext/hgmo/tests/commitextra.py
  > EOF

  $ echo p1_1 > foo
  $ hg commit -m 'push 1 commit 1'
  $ echo p1_2 > foo
  $ hg commit -m 'push 1 commit 2'
  $ hg -q push

  $ echo p2_1 > foo
  $ hg commit -m 'push 2 commit 1'
  $ echo p2_2 > foo
  $ hg commit -m 'push 2 commit 2' --extra "git_commit=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
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

Only draft changesets from current push included when automationrelevantdraftancestors set.

  $ hg phase -f --public -r 3

  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

  $ hg --config hgmo.automationrelevantdraftancestors=true log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
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

  $ http http://localhost:$HGPORT/json-automationrelevance/tip --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
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
              "phase": "draft",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
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
                  "branch": "default",
                  "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
              },
              "files": [
                  "foo"
              ],
              "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "git_repo_url": "https://github.com/mozilla-firefox/firefox",
              "node": "61613b60aa5dd21e5332d10a06643446896d96fe",
              "parents": [
                  "13855aae8fb3291c663ff46a8510c0e3fa673a4c"
              ],
              "phase": "draft",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
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
              "node": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "parents": [
                  "61613b60aa5dd21e5332d10a06643446896d96fe"
              ],
              "phase": "draft",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "pushid": 3,
              "pushuser": "testuser",
              "rev": 5,
              "reviewers": []
          }
      ],
      "visible": true
  }

Backout a node

  $ cd ../client
  $ hg backout -r 5
  reverting foo
  changeset 6:3e99eef45431 backs out changeset 5:c0026f6c6502
  $ hg push
  pushing to http://$LOCALHOST:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files

  $ http http://localhost:$HGPORT/json-automationrelevance/3e99eef45431 --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
  {
      "changesets": [
          {
              "author": "test",
              "backsoutnodes": [
                  {
                      "node": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761"
                  }
              ],
              "bugs": [],
              "date": [
                  0.0,
                  0
              ],
              "desc": "Backed out changeset c0026f6c6502",
              "extra": {
                  "branch": "default"
              },
              "files": [
                  "foo"
              ],
              "node": "3e99eef454310155a6e77abb52c80b9e754bb521",
              "parents": [
                  "c0026f6c6502b2c7ba02438b01f5419d5b3cc761"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "3e99eef454310155a6e77abb52c80b9e754bb521",
              "pushid": 4,
              "pushuser": "testuser",
              "rev": 6,
              "reviewers": []
          }
      ],
      "visible": true
  }

Backedoutby information not displayed without `backouts=1`

  $ http http://localhost:$HGPORT/json-automationrelevance/c0026f6c6502 --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
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
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
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
                  "branch": "default",
                  "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
              },
              "files": [
                  "foo"
              ],
              "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "git_repo_url": "https://github.com/mozilla-firefox/firefox",
              "node": "61613b60aa5dd21e5332d10a06643446896d96fe",
              "parents": [
                  "13855aae8fb3291c663ff46a8510c0e3fa673a4c"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
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
              "node": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "parents": [
                  "61613b60aa5dd21e5332d10a06643446896d96fe"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "pushid": 3,
              "pushuser": "testuser",
              "rev": 5,
              "reviewers": []
          }
      ],
      "visible": true
  }

Adds `backouts=1` query string parameter to show backout information

  $ http http://localhost:$HGPORT/json-automationrelevance/c0026f6c6502?backouts=1 --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
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
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
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
                  "branch": "default",
                  "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
              },
              "files": [
                  "foo"
              ],
              "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "git_repo_url": "https://github.com/mozilla-firefox/firefox",
              "node": "61613b60aa5dd21e5332d10a06643446896d96fe",
              "parents": [
                  "13855aae8fb3291c663ff46a8510c0e3fa673a4c"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "pushid": 3,
              "pushuser": "testuser",
              "rev": 4,
              "reviewers": []
          },
          {
              "author": "test",
              "backedoutby": "3e99eef454310155a6e77abb52c80b9e754bb521",
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
              "node": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "parents": [
                  "61613b60aa5dd21e5332d10a06643446896d96fe"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "pushid": 3,
              "pushuser": "testuser",
              "rev": 5,
              "reviewers": []
          }
      ],
      "visible": true
  }

Revert a commit

  $ hg backout -r 4 -m 'Revert "push 2 commit 2"
  > 
  > This reverts commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.'
  merging foo
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  changeset 7:14edbee910b3 backs out changeset 4:61613b60aa5d
  $ hg push
  pushing to http://$LOCALHOST:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files

  $ http http://localhost:$HGPORT/json-automationrelevance/14edbee910b3 --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
  {
      "changesets": [
          {
              "author": "test",
              "backsoutnodes": [
                  {
                      "node": "61613b60aa5dd21e5332d10a06643446896d96fe"
                  }
              ],
              "bugs": [],
              "date": [
                  0.0,
                  0
              ],
              "desc": "Revert \"push 2 commit 2\"\n\nThis reverts commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.",
              "extra": {
                  "branch": "default"
              },
              "files": [
                  "foo"
              ],
              "node": "14edbee910b375ae3bff29976f2feb24c61e4673",
              "parents": [
                  "3e99eef454310155a6e77abb52c80b9e754bb521"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "14edbee910b375ae3bff29976f2feb24c61e4673",
              "pushid": 5,
              "pushuser": "testuser",
              "rev": 7,
              "reviewers": []
          }
      ],
      "visible": true
  }

Backedoutby information not displayed without `backouts=1`

  $ http http://localhost:$HGPORT/json-automationrelevance/61613b60aa5d --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
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
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
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
                  "branch": "default",
                  "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
              },
              "files": [
                  "foo"
              ],
              "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "git_repo_url": "https://github.com/mozilla-firefox/firefox",
              "node": "61613b60aa5dd21e5332d10a06643446896d96fe",
              "parents": [
                  "13855aae8fb3291c663ff46a8510c0e3fa673a4c"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "pushid": 3,
              "pushuser": "testuser",
              "rev": 4,
              "reviewers": []
          }
      ],
      "visible": true
  }

Adds `backouts=1` query string parameter to show backout information

  $ http http://localhost:$HGPORT/json-automationrelevance/61613b60aa5d?backouts=1 --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
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
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "pushid": 3,
              "pushuser": "testuser",
              "rev": 3,
              "reviewers": []
          },
          {
              "author": "test",
              "backedoutby": "14edbee910b375ae3bff29976f2feb24c61e4673",
              "backsoutnodes": [],
              "bugs": [],
              "date": [
                  0.0,
                  0
              ],
              "desc": "push 2 commit 2",
              "extra": {
                  "branch": "default",
                  "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
              },
              "files": [
                  "foo"
              ],
              "git_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
              "git_repo_url": "https://github.com/mozilla-firefox/firefox",
              "node": "61613b60aa5dd21e5332d10a06643446896d96fe",
              "parents": [
                  "13855aae8fb3291c663ff46a8510c0e3fa673a4c"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushhead": "c0026f6c6502b2c7ba02438b01f5419d5b3cc761",
              "pushid": 3,
              "pushuser": "testuser",
              "rev": 4,
              "reviewers": []
          }
      ],
      "visible": true
  }


Web command for exposing just the changed files in a push works.

  $ echo a > a
  $ hg add a
  $ hg commit -m "add a"
  $ echo b > b
  $ hg add b
  $ hg commit -m "add b"
  $ echo c > c
  $ hg add c
  $ echo d > d
  $ hg add d
  $ hg commit -m "add c and d"
  $ hg push
  pushing to http://$LOCALHOST:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 3 changesets with 4 changes to 4 files

  $ http http://localhost:$HGPORT/json-pushchangedfiles/tip --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
  {
      "files": [
          "a",
          "b",
          "c",
          "d"
      ]
  }


Confirm no errors in log

  $ cd ../server
  $ cat error.log
