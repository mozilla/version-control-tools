  $ . $TESTDIR/hgext/pushlog/tests/helpers.sh

  $ cat >> $HGRCPATH << EOF
  > [experimental]
  > evolution = all
  > [extensions]
  > rebase =
  > EOF

  $ hg init server
  $ cd server
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > pushlog-feed = $TESTDIR/hgext/pushlog/feed.py
  > [phases]
  > publish = false
  > [web]
  > templates = $TESTDIR/hgtemplates
  > style = gitweb_mozilla
  > EOF

  $ wsgiconfig config.wsgi
  $ hg serve -d -p $HGPORT --pid-file hg.pid -A access.log -E error.log --web-conf config.wsgi
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

  $ export USER=user@example.com

  $ hg -q clone --pull server client
  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push
  recorded push in pushlog
  $ touch file0
  $ hg -q commit -A -m file0
  $ touch file1
  $ hg -q commit -A -m file1
  $ hg -q push
  recorded push in pushlog
  $ hg -q up -r 0
  $ touch file2
  $ hg -q commit -A -m file2
  $ touch file3
  $ hg -q commit -A -m file3
  $ hg push -f
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files (+1 heads)
  recorded push in pushlog

  $ hg rebase -s ae13d9da6966 -d 62eebb2f0f00
  rebasing 1:ae13d9da6966 "file0"
  rebasing 2:d313a202a85e "file1"
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 0 changes to 2 files
  recorded push in pushlog
  2 new obsolescence markers
  obsoleted 2 changesets (?)

Hidden changesets exposed as list under obsoletechangesets in version 1

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?version=1"
  200
  {
      "1": {
          "changesets": [
              "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      },
      "2": {
          "changesets": [],
          "date": \d+, (re)
          "obsoletechangesets": [
              "ae13d9da6966307c98b60987fb4fedc2e2f29736",
              "d313a202a85e114000f669c2fcb49ad42376ac04"
          ],
          "user": "user@example.com"
      },
      "3": {
          "changesets": [
              "b3641753ee63b166fad7c5f10060b0cbbc8a86b0",
              "62eebb2f0f00195f9d965f718090c678c4fa414d"
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      },
      "4": {
          "changesets": [
              "418a63f508062fb2eb9130065c5ddc7908dd5949",
              "d129109168f0ed985e51b0f86df256acdcfcfe45"
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      }
  }

obsolete changeset metadata exposed under full with version 1

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?version=1&full=1"
  200
  {
      "1": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "initial",
                  "files": [
                      "foo"
                  ],
                  "node": "96ee1d7354c4ad7372047672c36a1f561e3a6a4c",
                  "parents": [
                      "0000000000000000000000000000000000000000"
                  ],
                  "tags": []
              }
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      },
      "2": {
          "changesets": [],
          "date": \d+, (re)
          "obsoletechangesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file0",
                  "files": [
                      "file0"
                  ],
                  "node": "ae13d9da6966307c98b60987fb4fedc2e2f29736",
                  "parents": [
                      "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file1",
                  "files": [
                      "file1"
                  ],
                  "node": "d313a202a85e114000f669c2fcb49ad42376ac04",
                  "parents": [
                      "ae13d9da6966307c98b60987fb4fedc2e2f29736"
                  ],
                  "tags": []
              }
          ],
          "user": "user@example.com"
      },
      "3": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file2",
                  "files": [
                      "file2"
                  ],
                  "node": "b3641753ee63b166fad7c5f10060b0cbbc8a86b0",
                  "parents": [
                      "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file3",
                  "files": [
                      "file3"
                  ],
                  "node": "62eebb2f0f00195f9d965f718090c678c4fa414d",
                  "parents": [
                      "b3641753ee63b166fad7c5f10060b0cbbc8a86b0"
                  ],
                  "tags": []
              }
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      },
      "4": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file0",
                  "files": [
                      "file0"
                  ],
                  "node": "418a63f508062fb2eb9130065c5ddc7908dd5949",
                  "parents": [
                      "62eebb2f0f00195f9d965f718090c678c4fa414d"
                  ],
                  "precursors": [
                      "ae13d9da6966307c98b60987fb4fedc2e2f29736"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file1",
                  "files": [
                      "file1"
                  ],
                  "node": "d129109168f0ed985e51b0f86df256acdcfcfe45",
                  "parents": [
                      "418a63f508062fb2eb9130065c5ddc7908dd5949"
                  ],
                  "precursors": [
                      "d313a202a85e114000f669c2fcb49ad42376ac04"
                  ],
                  "tags": [
                      "tip"
                  ]
              }
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      }
  }

Hidden changesets exposed as list with version 2

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?version=2"
  200
  {
      "lastpushid": 4,
      "pushes": {
          "1": {
              "changesets": [
                  "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "2": {
              "changesets": [],
              "date": \d+, (re)
              "obsoletechangesets": [
                  "ae13d9da6966307c98b60987fb4fedc2e2f29736",
                  "d313a202a85e114000f669c2fcb49ad42376ac04"
              ],
              "user": "user@example.com"
          },
          "3": {
              "changesets": [
                  "b3641753ee63b166fad7c5f10060b0cbbc8a86b0",
                  "62eebb2f0f00195f9d965f718090c678c4fa414d"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "4": {
              "changesets": [
                  "418a63f508062fb2eb9130065c5ddc7908dd5949",
                  "d129109168f0ed985e51b0f86df256acdcfcfe45"
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          }
      }
  }

Hidden changeset metadata exposed under version 2 with full

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?version=2&full=1"
  200
  {
      "lastpushid": 4,
      "pushes": {
          "1": {
              "changesets": [
                  {
                      "author": "test",
                      "branch": "default",
                      "desc": "initial",
                      "files": [
                          "foo"
                      ],
                      "node": "96ee1d7354c4ad7372047672c36a1f561e3a6a4c",
                      "parents": [
                          "0000000000000000000000000000000000000000"
                      ],
                      "tags": []
                  }
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "2": {
              "changesets": [],
              "date": \d+, (re)
              "obsoletechangesets": [
                  {
                      "author": "test",
                      "branch": "default",
                      "desc": "file0",
                      "files": [
                          "file0"
                      ],
                      "node": "ae13d9da6966307c98b60987fb4fedc2e2f29736",
                      "parents": [
                          "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
                      ],
                      "tags": []
                  },
                  {
                      "author": "test",
                      "branch": "default",
                      "desc": "file1",
                      "files": [
                          "file1"
                      ],
                      "node": "d313a202a85e114000f669c2fcb49ad42376ac04",
                      "parents": [
                          "ae13d9da6966307c98b60987fb4fedc2e2f29736"
                      ],
                      "tags": []
                  }
              ],
              "user": "user@example.com"
          },
          "3": {
              "changesets": [
                  {
                      "author": "test",
                      "branch": "default",
                      "desc": "file2",
                      "files": [
                          "file2"
                      ],
                      "node": "b3641753ee63b166fad7c5f10060b0cbbc8a86b0",
                      "parents": [
                          "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
                      ],
                      "tags": []
                  },
                  {
                      "author": "test",
                      "branch": "default",
                      "desc": "file3",
                      "files": [
                          "file3"
                      ],
                      "node": "62eebb2f0f00195f9d965f718090c678c4fa414d",
                      "parents": [
                          "b3641753ee63b166fad7c5f10060b0cbbc8a86b0"
                      ],
                      "tags": []
                  }
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          },
          "4": {
              "changesets": [
                  {
                      "author": "test",
                      "branch": "default",
                      "desc": "file0",
                      "files": [
                          "file0"
                      ],
                      "node": "418a63f508062fb2eb9130065c5ddc7908dd5949",
                      "parents": [
                          "62eebb2f0f00195f9d965f718090c678c4fa414d"
                      ],
                      "precursors": [
                          "ae13d9da6966307c98b60987fb4fedc2e2f29736"
                      ],
                      "tags": []
                  },
                  {
                      "author": "test",
                      "branch": "default",
                      "desc": "file1",
                      "files": [
                          "file1"
                      ],
                      "node": "d129109168f0ed985e51b0f86df256acdcfcfe45",
                      "parents": [
                          "418a63f508062fb2eb9130065c5ddc7908dd5949"
                      ],
                      "precursors": [
                          "d313a202a85e114000f669c2fcb49ad42376ac04"
                      ],
                      "tags": [
                          "tip"
                      ]
                  }
              ],
              "date": \d+, (re)
              "user": "user@example.com"
          }
      }
  }

Hidden changesets dropped in feed

  $ http --no-headers "http://localhost:$HGPORT/server/atom-pushlog"
  200
  
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://*:$HGPORT/server/pushlog</id> (glob)
   <link rel="self" href="http://*:$HGPORT/server/pushlog"/> (glob)
   <link rel="alternate" href="http://*:$HGPORT/server/pushloghtml"/> (glob)
   <title>server Pushlog</title>
   <updated>*Z</updated> (glob)
   <entry>
    <title>Changeset d129109168f0ed985e51b0f86df256acdcfcfe45</title>
    <id>http://www.selenic.com/mercurial/#changeset-d129109168f0ed985e51b0f86df256acdcfcfe45</id>
    <link href="http://*:$HGPORT/server/rev/d129109168f0ed985e51b0f86df256acdcfcfe45"/> (glob)
    <updated>*Z</updated> (glob)
    <author>
     <name>user@example.com</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">file1</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 418a63f508062fb2eb9130065c5ddc7908dd5949</title>
    <id>http://www.selenic.com/mercurial/#changeset-418a63f508062fb2eb9130065c5ddc7908dd5949</id>
    <link href="http://*:$HGPORT/server/rev/418a63f508062fb2eb9130065c5ddc7908dd5949"/> (glob)
    <updated>*Z</updated> (glob)
    <author>
     <name>user@example.com</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">file0</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 62eebb2f0f00195f9d965f718090c678c4fa414d</title>
    <id>http://www.selenic.com/mercurial/#changeset-62eebb2f0f00195f9d965f718090c678c4fa414d</id>
    <link href="http://*:$HGPORT/server/rev/62eebb2f0f00195f9d965f718090c678c4fa414d"/> (glob)
    <updated>*Z</updated> (glob)
    <author>
     <name>user@example.com</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">file3</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset b3641753ee63b166fad7c5f10060b0cbbc8a86b0</title>
    <id>http://www.selenic.com/mercurial/#changeset-b3641753ee63b166fad7c5f10060b0cbbc8a86b0</id>
    <link href="http://*:$HGPORT/server/rev/b3641753ee63b166fad7c5f10060b0cbbc8a86b0"/> (glob)
    <updated>*Z</updated> (glob)
    <author>
     <name>user@example.com</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">file2</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset d313a202a85e114000f669c2fcb49ad42376ac04</title>
    <id>http://www.selenic.com/mercurial/#changeset-d313a202a85e114000f669c2fcb49ad42376ac04</id>
    <link href="http://*:$HGPORT/server/rev/d313a202a85e114000f669c2fcb49ad42376ac04"/> (glob)
    <updated>*Z</updated> (glob)
    <author>
     <name>user@example.com</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">file2</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset ae13d9da6966307c98b60987fb4fedc2e2f29736</title>
    <id>http://www.selenic.com/mercurial/#changeset-ae13d9da6966307c98b60987fb4fedc2e2f29736</id>
    <link href="http://*:$HGPORT/server/rev/ae13d9da6966307c98b60987fb4fedc2e2f29736"/> (glob)
    <updated>*Z</updated> (glob)
    <author>
     <name>user@example.com</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">file2</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 96ee1d7354c4ad7372047672c36a1f561e3a6a4c</title>
    <id>http://www.selenic.com/mercurial/#changeset-96ee1d7354c4ad7372047672c36a1f561e3a6a4c</id>
    <link href="*:$HGPORT/server/rev/96ee1d7354c4ad7372047672c36a1f561e3a6a4c"/> (glob)
    <updated>*Z</updated> (glob)
    <author>
     <name>user@example.com</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">foo</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>
  

Specifying a fromchange with a hidden changeset works

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?fromchange=d313a202a85e"
  200
  {
      "3": {
          "changesets": [
              "b3641753ee63b166fad7c5f10060b0cbbc8a86b0",
              "62eebb2f0f00195f9d965f718090c678c4fa414d"
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      },
      "4": {
          "changesets": [
              "418a63f508062fb2eb9130065c5ddc7908dd5949",
              "d129109168f0ed985e51b0f86df256acdcfcfe45"
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      }
  }

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?fromchange=d313a202a85e&full=1"
  200
  {
      "3": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file2",
                  "files": [
                      "file2"
                  ],
                  "node": "b3641753ee63b166fad7c5f10060b0cbbc8a86b0",
                  "parents": [
                      "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file3",
                  "files": [
                      "file3"
                  ],
                  "node": "62eebb2f0f00195f9d965f718090c678c4fa414d",
                  "parents": [
                      "b3641753ee63b166fad7c5f10060b0cbbc8a86b0"
                  ],
                  "tags": []
              }
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      },
      "4": {
          "changesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file0",
                  "files": [
                      "file0"
                  ],
                  "node": "418a63f508062fb2eb9130065c5ddc7908dd5949",
                  "parents": [
                      "62eebb2f0f00195f9d965f718090c678c4fa414d"
                  ],
                  "precursors": [
                      "ae13d9da6966307c98b60987fb4fedc2e2f29736"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file1",
                  "files": [
                      "file1"
                  ],
                  "node": "d129109168f0ed985e51b0f86df256acdcfcfe45",
                  "parents": [
                      "418a63f508062fb2eb9130065c5ddc7908dd5949"
                  ],
                  "precursors": [
                      "d313a202a85e114000f669c2fcb49ad42376ac04"
                  ],
                  "tags": [
                      "tip"
                  ]
              }
          ],
          "date": \d+, (re)
          "user": "user@example.com"
      }
  }

Specifying a tochange with a hidden changeset works

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?startID=1&tochange=ae13d9da6966"
  200
  {
      "2": {
          "changesets": [],
          "date": \d+, (re)
          "obsoletechangesets": [
              "ae13d9da6966307c98b60987fb4fedc2e2f29736",
              "d313a202a85e114000f669c2fcb49ad42376ac04"
          ],
          "user": "user@example.com"
      }
  }

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?startID=1&tochange=ae13d9da6966&full=1"
  200
  {
      "2": {
          "changesets": [],
          "date": \d+, (re)
          "obsoletechangesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file0",
                  "files": [
                      "file0"
                  ],
                  "node": "ae13d9da6966307c98b60987fb4fedc2e2f29736",
                  "parents": [
                      "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file1",
                  "files": [
                      "file1"
                  ],
                  "node": "d313a202a85e114000f669c2fcb49ad42376ac04",
                  "parents": [
                      "ae13d9da6966307c98b60987fb4fedc2e2f29736"
                  ],
                  "tags": []
              }
          ],
          "user": "user@example.com"
      }
  }

Specifying a hidden changeset works

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?changeset=ae13d9da6966"
  200
  {
      "2": {
          "changesets": [],
          "date": \d+, (re)
          "obsoletechangesets": [
              "ae13d9da6966307c98b60987fb4fedc2e2f29736",
              "d313a202a85e114000f669c2fcb49ad42376ac04"
          ],
          "user": "user@example.com"
      }
  }

  $ httpjson "http://localhost:$HGPORT/server/json-pushes?changeset=ae13d9da6966&full=1"
  200
  {
      "2": {
          "changesets": [],
          "date": \d+, (re)
          "obsoletechangesets": [
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file0",
                  "files": [
                      "file0"
                  ],
                  "node": "ae13d9da6966307c98b60987fb4fedc2e2f29736",
                  "parents": [
                      "96ee1d7354c4ad7372047672c36a1f561e3a6a4c"
                  ],
                  "tags": []
              },
              {
                  "author": "test",
                  "branch": "default",
                  "desc": "file1",
                  "files": [
                      "file1"
                  ],
                  "node": "d313a202a85e114000f669c2fcb49ad42376ac04",
                  "parents": [
                      "ae13d9da6966307c98b60987fb4fedc2e2f29736"
                  ],
                  "tags": []
              }
          ],
          "user": "user@example.com"
      }
  }

Confirm no errors in log

  $ cat ../server/error.log
