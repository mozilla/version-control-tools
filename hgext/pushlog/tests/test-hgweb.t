  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > pushlog = $TESTDIR/hgext/pushlog
  > 
  > [web]
  > templates = $TESTDIR/hgtemplates
  > style = gitweb_mozilla
  > EOF

  $ alias http=$TESTDIR/testing/http-request.py

  $ cd ..

  $ export USER=user1@example.com
  $ hg -q clone server client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg -q push
  recorded push in pushlog
  $ echo second > foo
  $ hg commit -m second
  $ echo third > foo
  $ hg commit -m third
  $ export USER=user2@example.com
  $ hg -q push
  recorded push in pushlog

  $ cd ../server
  $ hg serve -d -p $HGPORT --pid-file hg.pid -E error.log
  $ cat hg.pid >> $DAEMON_PIDS

Push info should show up in changeset view

  $ http http://localhost:$HGPORT/rev/55482a6fb4b1 --body-file body > /dev/null
  $ grep push body
  <a href="/pushloghtml">pushlog</a> |
  <tr><td>push id</td><td><a href="/pushloghtml?changeset=55482a6fb4b1">1</a></td></tr>
  <tr><td>push user</td><td>user1@example.com</td></tr>
  <tr><td>push date</td><td>*</td></tr> (glob)

  $ http http://localhost:$HGPORT/rev/6c9721b3b4df --body-file body > /dev/null
  $ grep push body
  <a href="/pushloghtml">pushlog</a> |
  <tr><td>push id</td><td><a href="/pushloghtml?changeset=6c9721b3b4df">2</a></td></tr>
  <tr><td>push user</td><td>user2@example.com</td></tr>
  <tr><td>push date</td><td>*</td></tr> (glob)

  $ http http://localhost:$HGPORT/log --body-file body > /dev/null
  $ grep push body
  <a href="/pushloghtml">pushlog</a> |
  Push <a href="/pushloghtml?changeset=82f53df85e9f">2</a> by user2@example.com at *<br /> (glob)
  Push <a href="/pushloghtml?changeset=6c9721b3b4df">2</a> by user2@example.com at *<br /> (glob)
  Push <a href="/pushloghtml?changeset=55482a6fb4b1">1</a> by user1@example.com at *<br /> (glob)

pushhead() works in search

  $ http "http://localhost:$HGPORT/json-log?rev=pushhead()" --body-file body > /dev/null
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
              "desc": "third",
              "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
              "parents": [
                  "6c9721b3b4dfc8c1f2d3103595e8bb2ffe5b8ff2"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 2,
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
              "desc": "initial",
              "node": "55482a6fb4b1881fa8f746fd52cf6f096bb21c89",
              "parents": [],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 1,
              "tags": [],
              "user": "test"
          }
      ],
      "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
      "query": "pushhead()"
  }

pushdate() works in search

  $ http "http://localhost:$HGPORT/json-log?rev=pushdate('>2017')" --body-file body > /dev/null
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
              "desc": "third",
              "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
              "parents": [
                  "6c9721b3b4dfc8c1f2d3103595e8bb2ffe5b8ff2"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 2,
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
              "desc": "second",
              "node": "6c9721b3b4dfc8c1f2d3103595e8bb2ffe5b8ff2",
              "parents": [
                  "55482a6fb4b1881fa8f746fd52cf6f096bb21c89"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
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
              "desc": "initial",
              "node": "55482a6fb4b1881fa8f746fd52cf6f096bb21c89",
              "parents": [],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 1,
              "tags": [],
              "user": "test"
          }
      ],
      "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
      "query": "pushdate('>2017')"
  }

pushuser() works in search

  $ http "http://localhost:$HGPORT/json-log?rev=pushuser(user1)" --body-file body > /dev/null
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
              "desc": "initial",
              "node": "55482a6fb4b1881fa8f746fd52cf6f096bb21c89",
              "parents": [],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 1,
              "tags": [],
              "user": "test"
          }
      ],
      "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
      "query": "pushuser(user1)"
  }

pushid() works in search

  $ http "http://localhost:$HGPORT/json-log?rev=pushid(1)" --body-file body > /dev/null
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
              "desc": "initial",
              "node": "55482a6fb4b1881fa8f746fd52cf6f096bb21c89",
              "parents": [],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 1,
              "tags": [],
              "user": "test"
          }
      ],
      "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
      "query": "pushid(1)"
  }

  $ http "http://localhost:$HGPORT/json-log?rev=pushid(3)" --body-file body > /dev/null
  $ python -m json.tool < body
  {
      "entries": [],
      "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
      "query": "pushid(3)"
  }

pushrev() works in search

  $ http "http://localhost:$HGPORT/json-log?rev=pushrev(1)" --body-file body > /dev/null
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
              "desc": "third",
              "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
              "parents": [
                  "6c9721b3b4dfc8c1f2d3103595e8bb2ffe5b8ff2"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 2,
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
              "desc": "second",
              "node": "6c9721b3b4dfc8c1f2d3103595e8bb2ffe5b8ff2",
              "parents": [
                  "55482a6fb4b1881fa8f746fd52cf6f096bb21c89"
              ],
              "phase": "public",
              "pushdate": [
                  \d+, (re)
                  0
              ],
              "pushid": 2,
              "tags": [],
              "user": "test"
          }
      ],
      "node": "82f53df85e9f23d81dbcfbf7debf9900cdc1e2ce",
      "query": "pushrev(1)"
  }

Confirm no errors in log

  $ cat error.log
