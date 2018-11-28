  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > 
  > [experimental]
  > httppeer.advertise-v2 = true
  > httppeer.v2-encoder-order = identity
  > EOF

  $ hg init server

  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [experimental]
  > web.apiserver = true
  > web.api.http-v2 = true
  > EOF

  $ echo 0 > foo
  $ hg -q commit -A -m initial

  $ echo 1 > foo
  $ hg commit -m 1
  $ hg tag tag-a
  $ hg up 0
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg branch new-branch
  marked working directory as branch new-branch
  (branches are permanent and global, did you want a bookmark?)
  $ echo 2 > foo
  $ hg commit -m 2
  $ hg tag tag-b

  $ hg branches
  new-branch                     4:ab082b0d7b76
  default                        2:52a7bad454df
  $ hg tags
  tip                                4:ab082b0d7b76
  tag-b                              3:09aec0ddabfc
  tag-a                              1:de3201cbb223

  $ ls .hg/cache/
  branch2-served
  checkisexec
  checklink
  checklink-target
  checknoexec
  hgtagsfnodes1
  manifestfulltextcache
  rbc-names-v1
  rbc-revs-v1
  tags2-visible

  $ hg serve -d --pid-file hg.pid -p $HGPORT -E error.log
  $ cat hg.pid >> $DAEMON_PIDS

Fetching all cache files works

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command mozrawcachefiles
  > EOF
  creating http peer for wire protocol version 2
  sending mozrawcachefiles command
  response: gen[
    {
      b'filecount': 5,
      b'totalsize': 463
    },
    {
      b'location': b'cache',
      b'path': b'branch2-served',
      b'size': 148
    },
    b'ab082b0d7b7638b99fe592e5dece8b1f4ec33122 4\n52a7bad454df6e92890c67cbd31f5864ddd1957c o default\nab082b0d7b7638b99fe592e5dece8b1f4ec33122 o new-branch\n',
    b'',
    {
      b'location': b'cache',
      b'path': b'rbc-names-v1',
      b'size': 18
    },
    b'default\x00new-branch',
    b'',
    {
      b'location': b'cache',
      b'path': b'rbc-revs-v1',
      b'size': 40
    },
    b'h\x98b\x13\x00\x00\x00\x00\xde2\x01\xcb\x00\x00\x00\x00R\xa7\xba\xd4\x00\x00\x00\x00\t\xae\xc0\xdd\x00\x00\x00\x01\xab\x08+\r\x00\x00\x00\x01',
    b'',
    {
      b'location': b'cache',
      b'path': b'tags2-visible',
      b'size': 137
    },
    b'4 ab082b0d7b7638b99fe592e5dece8b1f4ec33122\nde3201cbb223d261c9528e533ac4012a6f3cdb16 tag-a\n09aec0ddabfcae0346aec5c8c81380d638063965 tag-b\n',
    b'',
    {
      b'location': b'cache',
      b'path': b'hgtagsfnodes1',
      b'size': 120
    },
    b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xffR\xa7\xba\xd4S\xa8\x98Q\x8ah"Xk\x86\xd9H\x91!R\xeb\xd7\xd1\x97\xf1\t\xae\xc0\xdd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xab\x08+\rv\xdf\x82\xb6\xa7\x1f\xa5\xf8\x8b\x04/\xdd\xb5\xfc\xb5G\x11O\xbc\x85',
    b''
  ]

Fetching a subset of cache files works

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command mozrawcachefiles
  >     files eval:[b'branch2-served']
  > EOF
  creating http peer for wire protocol version 2
  sending mozrawcachefiles command
  response: gen[
    {
      b'filecount': 1,
      b'totalsize': 148
    },
    {
      b'location': b'cache',
      b'path': b'branch2-served',
      b'size': 148
    },
    b'ab082b0d7b7638b99fe592e5dece8b1f4ec33122 4\n52a7bad454df6e92890c67cbd31f5864ddd1957c o default\nab082b0d7b7638b99fe592e5dece8b1f4ec33122 o new-branch\n',
    b''
  ]

  $ cat error.log
