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
  $ cat > rmpd << EOF
  > import json
  > with open('body') as fd:
  >     data = json.load(fd)
  > n = 0.
  > for entry in data['entries']:
  >     entry['pushdate'] = [n, 0]
  >     n += 1
  > print json.dumps(data, indent = 4, sort_keys = True)
  > EOF
  $ python rmpd
  {
      "entries": [
          {
              "author": "test", 
              "date": [
                  0.0, 
                  0
              ], 
              "desc": "NO BUG", 
              "node": "313d9c157189179b5853d16831f80aa5ab609782", 
              "pushdate": [
                  0.0, 
                  0
              ], 
              "pushid": 3
          }, 
          {
              "author": "test", 
              "date": [
                  0.0, 
                  0
              ], 
              "desc": "Bug 159 - Do foo; r=calixte\n\nThis is related to bug 265.", 
              "node": "ca92ee64ee5df95ce203c3a1ba6c72a6328963d1", 
              "pushdate": [
                  1.0, 
                  0
              ], 
              "pushid": 2
          }, 
          {
              "author": "test", 
              "date": [
                  0.0, 
                  0
              ], 
              "desc": "Bug 314; r=calixte", 
              "node": "4de9924f06f2d653b28fda17113787fcfffb03e0", 
              "pushdate": [
                  2.0, 
                  0
              ], 
              "pushid": 1
          }
      ], 
      "file": "foo"
  }
