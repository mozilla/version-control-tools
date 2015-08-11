  $ . $TESTDIR/hgext/pushlog-legacy/tests/helpers.sh

  $ hg init server
  $ cd server
  $ serverconfig .hg/hgrc

  $ hg serve -d -p $HGPORT --pid-file hg.pid -A access.log -E error.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Create a repo with a few pushes

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push
  $ echo c1 > foo
  $ hg commit -m c1
  $ hg -q push
  $ hg -q up -r 0
  $ echo c2 > foo
  $ hg commit -m c2
  created new head
  $ hg -q push -f

Now strip a push so it is empty

  $ hg --config extensions.strip= -R ../server strip -r 1 --no-backup
  changeset will be deleted from pushlog: 5c7fc4be67eca7df5186bbc52dcb223fee2b6cbc
  changeset rev will be updated in pushlog: 059b473c43d7e25d6b6f5070dfb1c468b0e9518c

JSON output should render empty changeset array

  $ http "http://localhost:$HGPORT/json-pushes?startID=0" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "1": {
          "changesets": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "date": \d+, (re)
          "user": "*" (glob)
      },
      "3": {
          "changesets": [
              "059b473c43d7e25d6b6f5070dfb1c468b0e9518c"
          ],
          "date": \d+, (re)
          "user": "*" (glob)
      }
  }

Full output should do the same

  $ http "http://localhost:$HGPORT/json-pushes?startID=0&full=1" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "1": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "initial",
                  "files": [
                      "foo"
                  ],
                  "node": "96ee1d7354c4ad7372047672c36a1f561e3a6a4c",
                  "tags": []
              }
          ],
          "date": \d+, (re)
          "user": "*" (glob)
      },
      "3": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "c2",
                  "files": [
                      "foo"
                  ],
                  "node": "059b473c43d7e25d6b6f5070dfb1c468b0e9518c",
                  "tags": [
                      "tip"
                  ]
              }
          ],
          "date": \d+, (re)
          "user": "*" (glob)
      }
  }
