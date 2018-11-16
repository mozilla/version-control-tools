#require motoserver

  $ . $TESTDIR/hgext/wireprotocache/tests/wireprotohelpers.sh

Set up the mock S3 server, create a bucket

  $ moto_server -p $HGPORT1 s3 >> mocks3.log 2>&1 &
  $ MOTO_PID=$!
  $ echo $MOTO_PID >> $DAEMON_PIDS
  >>> import boto3
  >>> s3 = boto3.client('s3',
  ... aws_access_key_id='dummyaccessid',
  ... aws_secret_access_key='dummysecretkey',
  ... endpoint_url='http://localhost:$HGPORT1/')
  >>> _ = s3.create_bucket(
  ... ACL='public-read',
  ... Bucket='testbucket')

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > blackbox =
  > [blackbox]
  > track = wireprotocache
  > EOF
  $ hg init server
  $ enablehttpv2 server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > wireprotocache = $TESTDIR/hgext/wireprotocache
  > [wireprotocache]
  > plugin = s3
  > [wireprotocache.s3]
  > access-key-id = dummyaccessid
  > secret-access-key = dummysecretkey
  > bucket = testbucket
  > redirecttargets = http://localhost:$HGPORT1/
  > endpoint_url = http://localhost:$HGPORT1/
  > delete-repo-keystate = True
  > EOF

  $ echo a0 > a
  $ echo b0 > b
  $ hg -q commit -A -m 'commit 0'
  $ echo a1 > a
  $ hg commit -m 'commit 1'
  $ echo b1 > b
  $ hg commit -m 'commit 2'
  $ echo a2 > a
  $ echo b2 > b
  $ hg commit -m 'commit 3'

  $ hg log -G -T '{rev}:{node} {desc}'
  @  3:50590a86f3ff5d1e9a1624a7a6957884565cc8e8 commit 3
  |
  o  2:4d01eda50c6ac5f7e89cbe1880143a32f559c302 commit 2
  |
  o  1:4432d83626e8a98655f062ec1f2a43b07f7fbbb0 commit 1
  |
  o  0:3390ef850073fbc2f0dfff2244342c8e9229013a commit 0
  
  $ hg --debug debugindex -m
     rev linkrev nodeid                                   p1                                       p2
       0       0 992f4779029a3df8d0666d00bb924f69634e2641 0000000000000000000000000000000000000000 0000000000000000000000000000000000000000
       1       1 a988fb43583e871d1ed5750ee074c6d840bbbfc8 992f4779029a3df8d0666d00bb924f69634e2641 0000000000000000000000000000000000000000
       2       2 a8853dafacfca6fc807055a660d8b835141a3bb4 a988fb43583e871d1ed5750ee074c6d840bbbfc8 0000000000000000000000000000000000000000
       3       3 3fe11dfbb13645782b0addafbe75a87c210ffddc a8853dafacfca6fc807055a660d8b835141a3bb4 0000000000000000000000000000000000000000

  $ hg serve -p $HGPORT -d --pid-file hg.pid -E error.log
  $ HGSERVEPID=`cat hg.pid`

  $ printf "\n" >> $DAEMON_PIDS
  $ cat hg.pid >> $DAEMON_PIDS

Performing the same request twice should produce the same result,
with the first request caching the response in S3 and the second
result coming as an S3 redirect

  $ sendhttpv2peer << EOF
  > command manifestdata
  >     nodes eval:[b'\x99\x2f\x47\x79\x02\x9a\x3d\xf8\xd0\x66\x6d\x00\xbb\x92\x4f\x69\x63\x4e\x26\x41']
  >     tree eval:b''
  >     fields eval:[b'parents']
  > EOF
  creating http peer for wire protocol version 2
  sending manifestdata command
  response: gen[
    {
      b'totalitems': 1
    },
    {
      b'node': b'\x99/Gy\x02\x9a=\xf8\xd0fm\x00\xbb\x92OicN&A',
      b'parents': [
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
      ]
    }
  ]

  $ sendhttpv2peer << EOF
  > command manifestdata
  >     nodes eval:[b'\x99\x2f\x47\x79\x02\x9a\x3d\xf8\xd0\x66\x6d\x00\xbb\x92\x4f\x69\x63\x4e\x26\x41']
  >     tree eval:b''
  >     fields eval:[b'parents']
  > EOF
  creating http peer for wire protocol version 2
  sending manifestdata command
  response: gen[
    {
      b'totalitems': 1
    },
    {
      b'node': b'\x99/Gy\x02\x9a=\xf8\xd0fm\x00\xbb\x92OicN&A',
      b'parents': [
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
      ]
    }
  ]

  $ cat .hg/blackbox.log
  *> s3 cacher constructed for manifestdata (glob)
  *> 47abb8efa5f01b8964d74917793ad2464db0fa2c: cache miss (glob)
  *> 47abb8efa5f01b8964d74917793ad2464db0fa2c: storing cache entry (glob)
  *> s3 cacher constructed for manifestdata (glob)
  *> 47abb8efa5f01b8964d74917793ad2464db0fa2c: cache hit, creating redirect response (glob)
  .+> serving redirect response to http://localhost:$HGPORT1/testbucket/47abb8efa5f01b8964d74917793ad2464db0fa2c\?(Signature=.+&?|Expires=\d+&?|AWSAccessKeyId=dummyaccessid&?){3}(re)
  
  $ rm .hg/blackbox.log

Sending different request doesn't yield cache hit.

  $ sendhttpv2peer << EOF
  > command manifestdata
  >     nodes eval:[b'\x99\x2f\x47\x79\x02\x9a\x3d\xf8\xd0\x66\x6d\x00\xbb\x92\x4f\x69\x63\x4e\x26\x41', b'\xa9\x88\xfb\x43\x58\x3e\x87\x1d\x1e\xd5\x75\x0e\xe0\x74\xc6\xd8\x40\xbb\xbf\xc8']
  >     tree eval:b''
  >     fields eval:[b'parents']
  > EOF
  creating http peer for wire protocol version 2
  sending manifestdata command
  response: gen[
    {
      b'totalitems': 2
    },
    {
      b'node': b'\x99/Gy\x02\x9a=\xf8\xd0fm\x00\xbb\x92OicN&A',
      b'parents': [
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
      ]
    },
    {
      b'node': b'\xa9\x88\xfbCX>\x87\x1d\x1e\xd5u\x0e\xe0t\xc6\xd8@\xbb\xbf\xc8',
      b'parents': [
        b'\x99/Gy\x02\x9a=\xf8\xd0fm\x00\xbb\x92OicN&A',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
      ]
    }
  ]

  $ cat .hg/blackbox.log
  *> s3 cacher constructed for manifestdata (glob)
  *> 37326a83e9843f15161fce9d1e92d06b795d5e8e: cache miss (glob)
  *> 37326a83e9843f15161fce9d1e92d06b795d5e8e: storing cache entry (glob)
  $ rm .hg/blackbox.log

Setting minimumobjectsize will make small requests avoid caching

  $ cat >> .hg/hgrc << EOL
  > minimumobjectsize = 50000
  > EOL
  $ kill $HGSERVEPID
  $ hg serve -p $HGPORT -d --pid-file hg.pid -E error.log
  $ printf "\n" >> $DAEMON_PIDS
  $ cat hg.pid >> $DAEMON_PIDS

  $ sendhttpv2peer << EOF
  > command manifestdata
  >     nodes eval:[b'\xa9\x88\xfb\x43\x58\x3e\x87\x1d\x1e\xd5\x75\x0e\xe0\x74\xc6\xd8\x40\xbb\xbf\xc8']
  >     tree eval:b''
  >     fields eval:[b'parents']
  > EOF
  creating http peer for wire protocol version 2
  sending manifestdata command
  response: gen[
    {
      b'totalitems': 1
    },
    {
      b'node': b'\xa9\x88\xfbCX>\x87\x1d\x1e\xd5u\x0e\xe0t\xc6\xd8@\xbb\xbf\xc8',
      b'parents': [
        b'\x99/Gy\x02\x9a=\xf8\xd0fm\x00\xbb\x92OicN&A',
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
      ]
    }
  ]

  $ cat .hg/blackbox.log
  *> s3 cacher constructed for manifestdata (glob)
  *> a5291ad0e900bc65a180a494f63587b5705f282f: cache miss (glob)
  *> obj size (91) is below minimum of 50000; not caching (glob)
  $ rm .hg/blackbox.log

Server error logs should be empty

  $ cat error.log

S3 logs should show hits/misses/redirects. Use a regex to parse the
presigned URL, since the order of query string parameters is not
deterministic.

  $ cat ../mocks3.log
   * Running on http://$LOCALIP:$HGPORT1/ (Press CTRL+C to quit)
  * "PUT /testbucket HTTP/1.1" 200 - (glob)
  * "HEAD /testbucket/47abb8efa5f01b8964d74917793ad2464db0fa2c HTTP/1.1" 404 - (glob)
  * "PUT /testbucket/47abb8efa5f01b8964d74917793ad2464db0fa2c HTTP/1.1" 200 - (glob)
  * "HEAD /testbucket/47abb8efa5f01b8964d74917793ad2464db0fa2c HTTP/1.1" 200 - (glob)
  \$LOCALIP - - \[.+\] "GET /testbucket/47abb8efa5f01b8964d74917793ad2464db0fa2c\?(Signature=.+&?|Expires=\d+&?|AWSAccessKeyId=dummyaccessid&?){3} HTTP/1.1" 200 - (re)
  * "HEAD /testbucket/37326a83e9843f15161fce9d1e92d06b795d5e8e HTTP/1.1" 404 - (glob)
  * "PUT /testbucket/37326a83e9843f15161fce9d1e92d06b795d5e8e HTTP/1.1" 200 - (glob)
  * "HEAD /testbucket/a5291ad0e900bc65a180a494f63587b5705f282f HTTP/1.1" 404 - (glob)

  $ rm ../mocks3.log
