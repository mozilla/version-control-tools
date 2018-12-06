  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > blackbox =
  > simplecache = $TESTDIR/pylib/mercurial-support/wireprotosimplecache.py
  > hgmo = $TESTDIR/hgext/hgmo
  > [blackbox]
  > track = simplecache
  > [simplecache]
  > cacheobjects = true
  > [experimental]
  > web.apiserver = true
  > web.api.http-v2 = true
  > httppeer.v2-encoder-order=identity
  > EOF

  $ hg init server
  $ cd server
  $ touch 0
  $ hg commit -A -m initial
  adding 0
  $ hg serve -p $HGPORT -d --pid-file hg.pid -E error.log
  $ cat hg.pid > $DAEMON_PIDS
  $ cd ..
Requesting just changelog data won't cache
  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command rawstorefiledata
  >     files eval:[b'changelog']
  > EOF
  creating http peer for wire protocol version 2
  sending rawstorefiledata command
  response: gen[
    {
      b'filecount': 1,
      b'totalsize': 125
    },
    {
      b'location': b'store',
      b'path': b'00changelog.i',
      b'size': 125
    },
    b'\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00=\x00\x00\x00<\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x0e\x93\x8a\x1c\'\xb1K87)\xba\xc2Q\xc6\\\x14\xd8\xf4\x11m\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00ua84de0447720be7560b237f1fb3f035c2393bd92\ntest\n0 0\n0\n\ninitial',
    b''
  ]

Requesting changelog + manifestlog will cache

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command rawstorefiledata
  >     files eval:[b'changelog', b'manifestlog']
  > EOF
  creating http peer for wire protocol version 2
  sending rawstorefiledata command
  response: gen[
    {
      b'filecount': 2,
      b'totalsize': 233
    },
    {
      b'location': b'store',
      b'path': b'00manifest.i',
      b'size': 108
    },
    b'\x00\x03\x00\x01\x00\x00\x00\x00\x00\x00\x00,\x00\x00\x00+\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xa8M\xe0Dw \xbeu`\xb27\xf1\xfb?\x03\\#\x93\xbd\x92\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00u0\x00b80de5d138758541c5f05265ad144ab9fa86d1db\n',
    b'',
    {
      b'location': b'store',
      b'path': b'00changelog.i',
      b'size': 125
    },
    b'\x00\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00=\x00\x00\x00<\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x0e\x93\x8a\x1c\'\xb1K87)\xba\xc2Q\xc6\\\x14\xd8\xf4\x11m\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00ua84de0447720be7560b237f1fb3f035c2393bd92\ntest\n0 0\n0\n\ninitial',
    b''
  ]

  $ hg debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/ << EOF
  > command rawstorefiledata
  >     files eval:[b'changelog', b'manifestlog']
  > EOF
  creating http peer for wire protocol version 2
  sending rawstorefiledata command
  response: gen[
    {
      b'filecount': 2,
      b'totalsize': 233
    },
    {
      b'location': b'store',
      b'path': b'00manifest.i',
      b'size': 108
    },
    b'',
    {
      b'location': b'store',
      b'path': b'00changelog.i',
      b'size': 125
    },
    b''
  ]

  $ cat server/.hg/blackbox.log
  *> cacher constructed for rawstorefiledata (glob)
  *> cacher constructed for rawstorefiledata (glob)
  *> cache miss for 6c88a9927560a12aae99033bf60a34a967512f55 (glob)
  *> storing cache entry for 6c88a9927560a12aae99033bf60a34a967512f55 (glob)
  *> cacher constructed for rawstorefiledata (glob)
  *> cache hit for 6c88a9927560a12aae99033bf60a34a967512f55 (glob)

  $ cat server/error.log
