  $ . $TESTDIR/hgext/pushlog/tests/helpers.sh

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > pushlog-feed = $TESTDIR/hgext/pushlog/feed.py
  > [web]
  > templates = $TESTDIR/hgtemplates
  > style = gitweb_mozilla
  > EOF

  $ wsgiconfig config.wsgi
  $ hg serve -d -p $HGPORT --pid-file hg.pid -A access.log -E error.log --web-conf config.wsgi
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ export USER=user@example.com


Add commits with git_commit extra and verify json-pushes shows them

  $ hg -q clone --pull server client-git
  $ cd client-git
  $ cat >> .hg/hgrc <<EOF
  > [extensions]
  > commitextra = $TESTDIR/hgext/hgmo/tests/commitextra.py
  > EOF

  $ echo a > a
  $ hg add a
  $ hg -q commit -m "add a" --extra "git_commit=1111111111111111111111111111111111111111"
  $ echo b > b
  $ hg add b
  $ hg -q commit -m "add b" --extra "git_commit=2222222222222222222222222222222222222222"
  $ echo c > c
  $ hg add c
  $ hg -q commit -m "add c"
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  recorded push in pushlog
  added 3 changesets with 3 changes to 3 files

Confirm git_changesets are included in JSON output

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?version=1"
  200
  {
      "1": {
          "changesets": [
              "f3e20a781c8fb68bf029420e208068f1d7336634",
              "fe461f7d48abf327611448ae2eb39bd7f80121c3",
              "843c7043b19a1608b094ffcf4be1de6c19abd7c2"
          ],
          "date": \d+, (re)
          "git_changesets": [
              "1111111111111111111111111111111111111111",
              "2222222222222222222222222222222222222222",
              null
          ],
          "user": "user@example.com"
      }
  }

Confirm git_node and git_parents are included in full=1 output

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?version=1&full=1"
  200
  {
      "1": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "add a",
                  "files": [
                      "a"
                  ],
                  "git_node": "1111111111111111111111111111111111111111",
                  "git_parents": [
                      null
                  ],
                  "node": "f3e20a781c8fb68bf029420e208068f1d7336634",
                  "parents": [
                      "0000000000000000000000000000000000000000"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "add b",
                  "files": [
                      "b"
                  ],
                  "git_node": "2222222222222222222222222222222222222222",
                  "git_parents": [
                      "1111111111111111111111111111111111111111"
                  ],
                  "node": "fe461f7d48abf327611448ae2eb39bd7f80121c3",
                  "parents": [
                      "f3e20a781c8fb68bf029420e208068f1d7336634"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "add c",
                  "files": [
                      "c"
                  ],
                  "git_node": null,
                  "git_parents": [
                      "2222222222222222222222222222222222222222"
                  ],
                  "node": "843c7043b19a1608b094ffcf4be1de6c19abd7c2",
                  "parents": [
                      "fe461f7d48abf327611448ae2eb39bd7f80121c3"
                  ],
                  "tags": [
                      "tip"
                  ]
              }
          ],
          "date": \d+, (re)
          "git_changesets": [
              "1111111111111111111111111111111111111111",
              "2222222222222222222222222222222222222222",
              null
          ],
          "user": "user@example.com"
      }
  }
