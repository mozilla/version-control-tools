  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial

  $ echo 1 > foo
  $ hg commit -m 'commit 1'
  $ echo 2 > foo
  $ hg commit -m 'commit 2'
  $ echo 3 > foo
  $ hg commit -m 'commit 3'
  $ hg -q up 0
  $ echo 1a > foo
  $ hg commit -m 'head 2'
  created new head

  $ hg -q push

  $ hg log -G -T '{node} {desc}'
  @  45758e0a312e80929767af843ed1198ddeac8a15 head 2
  |
  | o  9e5bfe49e2794365d9dc3b8de60aff9777d64bd0 commit 3
  | |
  | o  66f9e202ac6e3fc4aff8424aff7ccb825339e4a7 commit 2
  | |
  | o  e4e891475ac0099835bb15a6b636adbdb85f753e commit 1
  |/
  o  55482a6fb4b1881fa8f746fd52cf6f096bb21c89 initial
  

Immediate parent returns true

  $ http "http://localhost:$HGPORT/json-isancestor/?head=9e5bfe49e2794365d9dc3b8de60aff9777d64bd0&node=66f9e202ac6e3fc4aff8424aff7ccb825339e4a7" --header content-type
  200
  content-type: application/json
  
  {
  "headnode": "9e5bfe49e2794365d9dc3b8de60aff9777d64bd0",
  "testnode": "66f9e202ac6e3fc4aff8424aff7ccb825339e4a7",
  "isancestor": true
  }

Grandparent returns true

  $ http "http://localhost:$HGPORT/json-isancestor/?head=9e5bfe49e2794365d9dc3b8de60aff9777d64bd0&node=e4e891475ac0099835bb15a6b636adbdb85f753e" --header content-type
  200
  content-type: application/json
  
  {
  "headnode": "9e5bfe49e2794365d9dc3b8de60aff9777d64bd0",
  "testnode": "e4e891475ac0099835bb15a6b636adbdb85f753e",
  "isancestor": true
  }

Node on other head isn't ancestor

  $ http "http://localhost:$HGPORT/json-isancestor/?head=9e5bfe49e2794365d9dc3b8de60aff9777d64bd0&node=45758e0a312e80929767af843ed1198ddeac8a15" --header content-type
  200
  content-type: application/json
  
  {
  "headnode": "9e5bfe49e2794365d9dc3b8de60aff9777d64bd0",
  "testnode": "45758e0a312e80929767af843ed1198ddeac8a15",
  "isancestor": false
  }

Self is ancestor of self

  $ http "http://localhost:$HGPORT/json-isancestor/?head=e4e891475ac0099835bb15a6b636adbdb85f753e&node=e4e891475ac0099835bb15a6b636adbdb85f753e" --header content-type
  200
  content-type: application/json
  
  {
  "headnode": "e4e891475ac0099835bb15a6b636adbdb85f753e",
  "testnode": "e4e891475ac0099835bb15a6b636adbdb85f753e",
  "isancestor": true
  }

Unknown head revision raises reasonable error

  $ http "http://localhost:$HGPORT/json-isancestor/?head=foobar&node=9e5bfe49e2794365d9dc3b8de60aff9777d64bd0" --header content-type
  404
  content-type: application/json
  
  "unknown head revision foobar"

  $ cat ../server/error.log

Unknown test revision raises reasonable error

  $ http "http://localhost:$HGPORT/json-isancestor/?head=e4e891475ac0099835bb15a6b636adbdb85f753e&node=foobar" --header content-type
  404
  content-type: application/json
  
  "unknown node revision foobar"

Confirm no errors in log

  $ cat ../server/error.log
