  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh

  $ startserver

  $ hg clone http://localhost:$HGPORT repo
  no changes found
  updating to branch default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd repo
  $ touch foo
  $ hg -q commit -A -m initial
  $ echo second > foo
  $ hg commit -m second
  $ hg -q up -r 0
  $ echo head2 > bar
  $ hg commit -A -m head2
  adding bar
  created new head
  $ hg tag release1

  $ hg -q up -r 0
  $ hg branch new_branch
  marked working directory as branch new_branch
  (branches are permanent and global, did you want a bookmark?)
  $ touch branch
  $ hg commit -A -m new_branch
  adding branch

  $ hg push -f
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 5 changesets with 5 changes to 4 files (+2 heads)
  remote: recorded push in pushlog

json-info requires a rev argument

  $ http http://localhost:$HGPORT/json-info --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "error": "missing parameter 'node'"
  }

A regular commit

  $ http http://localhost:$HGPORT/json-info/96ee1d7354c4 --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "96ee1d7354c4": {
          "branch": "default",
          "children": [
              "75f01efc4bb4419cbc86560aa69b579e45bfbf97",
              "761494ef3bb176117cad95f7842ce96d3b54466d",
              "2ea2f52a79bad8c0aeb72d3c68cb333f4148b020"
          ],
          "date": "1970-01-01 00:00 +0000",
          "description": "initial",
          "files": [
              "foo"
          ],
          "node": "96ee1d7354c4ad7372047672c36a1f561e3a6a4c",
          "parents": [
              "0000000000000000000000000000000000000000"
          ],
          "rev": 0,
          "tags": [],
          "user": "test"
      }
  }

A commit with a tag

  $ http http://localhost:$HGPORT/json-info/761494ef3bb1 --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "761494ef3bb1": {
          "branch": "default",
          "children": [
              "5ae0b03fdd2228e86b2d01bec964e41dcb1b9e04"
          ],
          "date": "1970-01-01 00:00 +0000",
          "description": "head2",
          "files": [
              "bar"
          ],
          "node": "761494ef3bb176117cad95f7842ce96d3b54466d",
          "parents": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "rev": 2,
          "tags": [
              "release1"
          ],
          "user": "test"
      }
  }

A commit on a branch

  $ http http://localhost:$HGPORT/json-info/2ea2f52a79ba --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "2ea2f52a79ba": {
          "branch": "new_branch",
          "children": [],
          "date": "1970-01-01 00:00 +0000",
          "description": "new_branch",
          "files": [
              "branch"
          ],
          "node": "2ea2f52a79bad8c0aeb72d3c68cb333f4148b020",
          "parents": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "rev": 4,
          "tags": [
              "tip"
          ],
          "user": "test"
      }
  }

Multiple nodes

  $ http "http://localhost:$HGPORT/json-info?node=96ee1d7354c4&node=761494ef3bb1&node=2ea2f52a79ba" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "2ea2f52a79ba": {
          "branch": "new_branch",
          "children": [],
          "date": "1970-01-01 00:00 +0000",
          "description": "new_branch",
          "files": [
              "branch"
          ],
          "node": "2ea2f52a79bad8c0aeb72d3c68cb333f4148b020",
          "parents": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "rev": 4,
          "tags": [
              "tip"
          ],
          "user": "test"
      },
      "761494ef3bb1": {
          "branch": "default",
          "children": [
              "5ae0b03fdd2228e86b2d01bec964e41dcb1b9e04"
          ],
          "date": "1970-01-01 00:00 +0000",
          "description": "head2",
          "files": [
              "bar"
          ],
          "node": "761494ef3bb176117cad95f7842ce96d3b54466d",
          "parents": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "rev": 2,
          "tags": [
              "release1"
          ],
          "user": "test"
      },
      "96ee1d7354c4": {
          "branch": "default",
          "children": [
              "75f01efc4bb4419cbc86560aa69b579e45bfbf97",
              "761494ef3bb176117cad95f7842ce96d3b54466d",
              "2ea2f52a79bad8c0aeb72d3c68cb333f4148b020"
          ],
          "date": "1970-01-01 00:00 +0000",
          "description": "initial",
          "files": [
              "foo"
          ],
          "node": "96ee1d7354c4ad7372047672c36a1f561e3a6a4c",
          "parents": [
              "0000000000000000000000000000000000000000"
          ],
          "rev": 0,
          "tags": [],
          "user": "test"
      }
  }
