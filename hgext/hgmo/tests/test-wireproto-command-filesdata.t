  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > [experimental]
  > httppeer.advertise-v2 = true
  > httppeer.v2-encoder-order = identity
  > web.apiserver = true
  > web.api.http-v2 = true
  > EOF

  $ hg init server
  $ cd server
  $ touch foo
  $ hg -q commit -Am initial

  $ echo foo > dupe-file
  $ hg commit -Am 'dupe 1'
  adding dupe-file
  $ hg -q up -r 0
  $ echo foo > dupe-file
  $ hg commit -Am 'dupe 2'
  adding dupe-file
  created new head

  $ hg log -G -T '{rev}:{node} {desc}\n'
  @  2:639c8990d6a56cbc9531fb5940db0e2438f13362 dupe 2
  |
  | o  1:1681c33f9f8051cffd8c23a6d408182df8f3a166 dupe 1
  |/
  o  0:96ee1d7354c4ad7372047672c36a1f561e3a6a4c initial
  

  $ hg serve -p $HGPORT -d --pid-file hg.pid -E error.log
  $ cat hg.pid > $DAEMON_PIDS

Test behavior where a file node is introduced in 2 DAG heads

Request for changeset introducing filenode returns linknode as self

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command filesdata
  >     revisions eval:[{
  >         b'type': b'changesetexplicit',
  >         b'nodes': [
  >             b'\x16\x81\xc3\x3f\x9f\x80\x51\xcf\xfd\x8c\x23\xa6\xd4\x08\x18\x2d\xf8\xf3\xa1\x66',
  >         ]}]
  >     fields eval:[b'linknode']
  >     pathfilter eval:{b'include': [b'path:dupe-file']}
  > EOF
  creating http peer for wire protocol version 2
  sending filesdata command
  response: gen[
    {
      b'totalitems': 1,
      b'totalpaths': 1
    },
    {
      b'path': b'dupe-file',
      b'totalitems': 1
    },
    {
      b'linknode': b'\x16\x81\xc3?\x9f\x80Q\xcf\xfd\x8c#\xa6\xd4\x08\x18-\xf8\xf3\xa1f',
      b'node': b'.\xd2\xa3\x91*\x0b$P C\xea\xe8N\xe4\xb2y\xc1\x8b\x90\xdd'
    }
  ]

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command filesdata
  >     revisions eval:[{
  >         b'type': b'changesetexplicit',
  >         b'nodes': [
  >             b'\x16\x81\xc3\x3f\x9f\x80\x51\xcf\xfd\x8c\x23\xa6\xd4\x08\x18\x2d\xf8\xf3\xa1\x66',
  >         ]}]
  >     fields eval:[b'linknode']
  >     haveparents eval:True
  >     pathfilter eval:{b'include': [b'path:dupe-file']}
  > EOF
  creating http peer for wire protocol version 2
  sending filesdata command
  response: gen[
    {
      b'totalitems': 1,
      b'totalpaths': 1
    },
    {
      b'path': b'dupe-file',
      b'totalitems': 1
    },
    {
      b'linknode': b'\x16\x81\xc3?\x9f\x80Q\xcf\xfd\x8c#\xa6\xd4\x08\x18-\xf8\xf3\xa1f',
      b'node': b'.\xd2\xa3\x91*\x0b$P C\xea\xe8N\xe4\xb2y\xc1\x8b\x90\xdd'
    }
  ]

Request for changeset where recorded linknode isn't in DAG ancestry will get
rewritten accordingly

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command filesdata
  >     revisions eval:[{
  >         b'type': b'changesetexplicit',
  >         b'nodes': [
  >             b'\x63\x9c\x89\x90\xd6\xa5\x6c\xbc\x95\x31\xfb\x59\x40\xdb\x0e\x24\x38\xf1\x33\x62',
  >         ]}]
  >     fields eval:[b'linknode']
  >     pathfilter eval:{b'include': [b'path:dupe-file']}
  > EOF
  creating http peer for wire protocol version 2
  sending filesdata command
  response: gen[
    {
      b'totalitems': 1,
      b'totalpaths': 1
    },
    {
      b'path': b'dupe-file',
      b'totalitems': 1
    },
    {
      b'linknode': b'\x16\x81\xc3?\x9f\x80Q\xcf\xfd\x8c#\xa6\xd4\x08\x18-\xf8\xf3\xa1f',
      b'node': b'.\xd2\xa3\x91*\x0b$P C\xea\xe8N\xe4\xb2y\xc1\x8b\x90\xdd'
    }
  ]

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command filesdata
  >     revisions eval:[{
  >         b'type': b'changesetexplicit',
  >         b'nodes': [
  >             b'\x63\x9c\x89\x90\xd6\xa5\x6c\xbc\x95\x31\xfb\x59\x40\xdb\x0e\x24\x38\xf1\x33\x62',
  >         ]}]
  >     fields eval:[b'linknode']
  >     haveparents eval:True
  >     pathfilter eval:{b'include': [b'path:dupe-file']}
  > EOF
  creating http peer for wire protocol version 2
  sending filesdata command
  response: gen[
    {
      b'totalitems': 0,
      b'totalpaths': 0
    }
  ]

  $ cat error.log
