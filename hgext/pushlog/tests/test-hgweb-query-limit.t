  $ . $TESTDIR/hgext/pushlog/tests/helpers.sh

  $ hg init server
  $ cd server
  $ serverconfig .hg/hgrc
  $ cat >> .hg/hgrc << EOF
  > [pushlog]
  > maxquerypushes = 3
  > EOF
  $ cd ..

  $ export USER=user@example.com
  $ hg -q clone server client
  $ cd client
  $ for i in 1 2 3 4 5; do
  >   echo $i > foo
  >   hg -q commit -A -m "commit $i"
  >   hg -q push
  > done
  recorded push in pushlog
  recorded push in pushlog
  recorded push in pushlog
  recorded push in pushlog
  recorded push in pushlog
  $ cd ../server
  $ hg serve -d -p $HGPORT --pid-file hg.pid -E error.log
  $ cat hg.pid >> $DAEMON_PIDS

Range queries within the limit work

  $ http "http://localhost:$HGPORT/json-pushes?startID=2&version=2" --no-headers --body-file body
  200
  $ python -c 'import json; print(sorted(json.load(open("body"))["pushes"]))'
  ['3', '4', '5']

  $ http "http://localhost:$HGPORT/json-pushes?startID=0&endID=3&version=2&full=1" --no-headers --body-file body
  200
  $ python -c 'import json; print(sorted(json.load(open("body"))["pushes"]))'
  ['1', '2', '3']

Range queries matching more pushes than the limit are rejected

  $ http "http://localhost:$HGPORT/json-pushes?startID=0&version=2&full=1" --header content-type --body-file body
  400
  content-type: application/json
  $ cat body
  {
  "error": "query matches more than 3 pushes; narrow it with endID, tochange or enddate"
  } (no-eol)

  $ http "http://localhost:$HGPORT/json-pushes?fromchange=0&version=2" --no-headers --body-file body
  400

  $ http "http://localhost:$HGPORT/json-pushes?startdate=1970-01-01" --no-headers --body-file body
  400

  $ http "http://localhost:$HGPORT/pushloghtml?startID=0" --no-headers --body-file body
  400

The default query (most recent pushes) is not affected by the limit

  $ http "http://localhost:$HGPORT/json-pushes?version=2" --no-headers --body-file body
  200
  $ python -c 'import json; print(sorted(json.load(open("body"))["pushes"]))'
  ['1', '2', '3', '4', '5']

A limit of 0 disables the check

  $ hg serve -d -p $HGPORT1 --pid-file hg1.pid -E error1.log --config pushlog.maxquerypushes=0
  $ cat hg1.pid >> $DAEMON_PIDS
  $ http "http://localhost:$HGPORT1/json-pushes?startID=0&version=2" --no-headers --body-file body
  200
  $ python -c 'import json; print(sorted(json.load(open("body"))["pushes"]))'
  ['1', '2', '3', '4', '5']

  $ cat error.log error1.log
