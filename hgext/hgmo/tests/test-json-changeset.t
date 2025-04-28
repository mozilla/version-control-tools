  $ export USER=hguser
  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client

  $ echo initial > foo
  $ hg -q commit -A -m 'Bug 271; r=calixte'
  $ hg -q push
  $ echo second > foo
  $ cat > message << EOF
  > Bug 828 - Do foo; r=calixte
  > 
  > This is related to bug 182.
  > EOF
  $ hg commit -l message
  $ hg -q push

  $ echo third > foo
  $ hg commit -m 'NO BUG'

  $ hg -q push

Last changeset

  $ http http://localhost:$HGPORT/json-rev/tip --header content-type --body-file body
  200
  content-type: application/json

  $ ppjson < body
  {
      "backedoutby": "",
      "bookmarks": [],
      "branch": "default",
      "children": [],
      "date": [
          0.0,
          0
      ],
      "desc": "NO BUG",
      "diff": [
          {
              "blockno": 1,
              "lines": [
                  {
                      "l": "--- a/foo\tThu Jan 01 00:00:00 1970 +0000\n",
                      "n": 1,
                      "t": "-"
                  },
                  {
                      "l": "+++ b/foo\tThu Jan 01 00:00:00 1970 +0000\n",
                      "n": 2,
                      "t": "+"
                  },
                  {
                      "l": "@@ -1,1 +1,1 @@\n",
                      "n": 3,
                      "t": "@"
                  },
                  {
                      "l": "-second\n",
                      "n": 4,
                      "t": "-"
                  },
                  {
                      "l": "+third\n",
                      "n": 5,
                      "t": "+"
                  }
              ]
          }
      ],
      "files": [
          {
              "file": "foo",
              "status": "modified"
          }
      ],
      "git_commit": null,
      "landingsystem": null,
      "node": "c761ad6d27c96f72f7e4637789e967c3f9730255",
      "parents": [
          "ef0e7ae3b607356f580e6d7671abea63db849cc2"
      ],
      "phase": "public",
      "pushdate": [
          \d+, (re)
          \d+ (re)
      ],
      "pushid": 3,
      "pushuser": "hguser",
      "tags": [
          "tip"
      ],
      "user": "test"
  }

Confirm no errors in log

  $ cat ../server/error.log
