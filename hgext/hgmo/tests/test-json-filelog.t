  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m 'Bug 314; r=calixte'
  $ hg -q push
  $ echo second > foo
  $ cat > message << EOF
  > Bug 159 - Do foo; r=calixte
  > 
  > This is related to bug 265.
  > EOF
  $ hg commit -l message
  $ hg -q push

  $ echo third > foo
  $ hg commit -m 'NO BUG'

  $ hg -q push

Single file with 3 commits

  $ http "http://localhost:$HGPORT/json-filelog?file=foo&node=tip" --header content-type --body-file body
  200
  content-type: application/json
  $ python -m json.tool < body
  {
      "entries": [
          {
              "bookmarks": [],
              "branch": "default",
              "date": [
                  0.0,
                  0
              ],
              "desc": "NO BUG",
              "node": "313d9c157189179b5853d16831f80aa5ab609782",
              "parents": [
                  "ca92ee64ee5df95ce203c3a1ba6c72a6328963d1"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  \d+ (re)
              ],
              "pushid": 3,
              "tags": [
                  "tip"
              ],
              "user": "test"
          },
          {
              "bookmarks": [],
              "branch": "default",
              "date": [
                  0.0,
                  0
              ],
              "desc": "Bug 159 - Do foo; r=calixte\n\nThis is related to bug 265.",
              "node": "ca92ee64ee5df95ce203c3a1ba6c72a6328963d1",
              "parents": [
                  "4de9924f06f2d653b28fda17113787fcfffb03e0"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  \d+ (re)
              ],
              "pushid": 2,
              "tags": [],
              "user": "test"
          },
          {
              "bookmarks": [],
              "branch": "default",
              "date": [
                  0.0,
                  0
              ],
              "desc": "Bug 314; r=calixte",
              "node": "4de9924f06f2d653b28fda17113787fcfffb03e0",
              "parents": [],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  \d+ (re)
              ],
              "pushid": 1,
              "tags": [],
              "user": "test"
          }
      ]
  }

Confirm no errors in log

  $ cat ../server/error.log
