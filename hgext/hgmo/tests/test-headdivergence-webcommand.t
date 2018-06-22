  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

Simple setup

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial

  $ echo 1 > file1
  $ echo 1 > file2
  $ hg -q commit -A -m 'file1 and file2'
  $ echo 2 > file1
  $ hg commit -m file1
  $ echo 1 > file3
  $ hg -q commit -A -m file3
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 4 changesets with 5 changes to 4 files
  remote: recorded push in pushlog

  $ hg log -G -T '{node} {desc}\n'
  @  3c042dabdc9c32e8018d3ee6fc1893023ae82722 file3
  |
  o  1e02b4106d16ecd9c1cf808aeca595c796e32148 file1
  |
  o  fd6b007c818ba311437431b00b6d3e378d020415 file1 and file2
  |
  o  55482a6fb4b1881fa8f746fd52cf6f096bb21c89 initial
  

Ask for changes since initial and no files

  $ http http://localhost:$HGPORT/json-headdivergence/?node=55482a6fb4b1 --header content-type --body-file body
  200
  content-type: application/json
  $ python -m json.tool < body
  {
      "commitsbehind": 3,
      "filemerges": {},
      "filemergesignored": false
  }

Ask for changes since initial and relevant to file1

  $ http "http://localhost:$HGPORT/json-headdivergence/?node=55482a6fb4b1&p=file1" --header content-type --body-file body
  200
  content-type: application/json
  $ python -m json.tool < body
  {
      "commitsbehind": 3,
      "filemerges": {
          "file1": [
              "fd6b007c818ba311437431b00b6d3e378d020415",
              "1e02b4106d16ecd9c1cf808aeca595c796e32148"
          ]
      },
      "filemergesignored": false
  }

Ask for changes relevant to multiple files

  $ http "http://localhost:$HGPORT/json-headdivergence/?node=55482a6fb4b1&p=file1&p=file3" --header content-type --body-file body
  200
  content-type: application/json
  $ python -m json.tool < body
  {
      "commitsbehind": 3,
      "filemerges": {
          "file1": [
              "fd6b007c818ba311437431b00b6d3e378d020415",
              "1e02b4106d16ecd9c1cf808aeca595c796e32148"
          ],
          "file3": [
              "3c042dabdc9c32e8018d3ee6fc1893023ae82722"
          ]
      },
      "filemergesignored": false
  }

Creating another head more recent than old one will show changes from
that head

  $ hg -q up -r 0
  $ echo 1 > file1
  $ hg -q commit -A -m 'file1 head 2'
  $ hg -q push -f

  $ hg log -G -T '{node} {desc}\n'
  @  6ffcbd2361eddf3fea07b6d1f5152731934badad file1 head 2
  |
  | o  3c042dabdc9c32e8018d3ee6fc1893023ae82722 file3
  | |
  | o  1e02b4106d16ecd9c1cf808aeca595c796e32148 file1
  | |
  | o  fd6b007c818ba311437431b00b6d3e378d020415 file1 and file2
  |/
  o  55482a6fb4b1881fa8f746fd52cf6f096bb21c89 initial
  

  $ http "http://localhost:$HGPORT/json-headdivergence/?node=55482a6fb4b1&p=file1" --header content-type --body-file body
  200
  content-type: application/json
  $ python -m json.tool < body
  {
      "commitsbehind": 1,
      "filemerges": {
          "file1": [
              "6ffcbd2361eddf3fea07b6d1f5152731934badad"
          ]
      },
      "filemergesignored": false
  }

Verify headdivergencemaxnodes limit works

  $ touch dummy
  $ hg -q commit -A -m dummy
  $ hg -q push
  $ cd ../server

  $ hg --config hgmo.headdivergencemaxnodes=1 serve -d -p $HGPORT1 --pid-file hg.pid --hgmo
  $ cat hg.pid >> $DAEMON_PIDS

  $ http "http://localhost:$HGPORT1/json-headdivergence/?node=55482a6fb4b1&p=file1" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "commitsbehind": 2,
      "filemerges": {},
      "filemergesignored": true
  }

Confirm no errors in log

  $ cat error.log
