  $ . $TESTDIR/hgext/pushlog-legacy/tests/helpers.sh

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
  > pushlog-feed = $TESTDIR/hgext/pushlog-legacy/pushlog-feed.py
  > [phases]
  > publish = false
  > [web]
  > templates = $TESTDIR/hgtemplates
  > style = gitweb_mozilla
  > EOF

  $ hg serve -d -p $HGPORT --pid-file hg.pid -A access.log -E error.log
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

FIXME Hidden changesets should not be exposed to version 1

  $ httpjson "http://localhost:$HGPORT/json-pushes?version=1"
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
          "changesets": [
              "ae13d9da6966307c98b60987fb4fedc2e2f29736",
              "d313a202a85e114000f669c2fcb49ad42376ac04"
          ],
          "date": \d+, (re)
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

  $ httpjson "http://localhost:$HGPORT/json-pushes?version=1&full=1"
  404
  "hidden revision 'd313a202a85e114000f669c2fcb49ad42376ac04'"

FIXME Hidden changesets should not be exposed to version 2

  $ httpjson "http://localhost:$HGPORT/json-pushes?version=2"
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
              "changesets": [
                  "ae13d9da6966307c98b60987fb4fedc2e2f29736",
                  "d313a202a85e114000f669c2fcb49ad42376ac04"
              ],
              "date": \d+, (re)
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

  $ httpjson "http://localhost:$HGPORT/json-pushes?version=2&full=1"
  404
  "hidden revision 'd313a202a85e114000f669c2fcb49ad42376ac04'"

FIXME Hidden changesets handled properly on feed

  $ http --no-headers "http://localhost:$HGPORT/atom-pushlog"
  404
  
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <!-- Error -->
   <id>http://*:$HGPORT/</id> (glob)
   <link rel="self" href="http://*:$HGPORT/atom-log"/> (glob)
   <link rel="alternate" href="http://*:$HGPORT/"/> (glob)
   <title>Error</title>
   <updated>1970-01-01T00:00:00+00:00</updated>
   <entry>
    <title>Error</title>
    <id>https://mercurial-scm.org/#error</id>
    <author>
      <name>mercurial</name>
    </author>
    <updated>1970-01-01T00:00:00+00:00</updated>
    <content type="text">hidden revision 'd313a202a85e114000f669c2fcb49ad42376ac04'</content>
   </entry>
  </feed>
  

FIXME Specifying a fromchange with a hidden changeset works

  $ httpjson "http://localhost:$HGPORT/json-pushes?fromchange=d313a202a85e"
  404
  "hidden revision 'd313a202a85e'"

  $ httpjson "http://localhost:$HGPORT/json-pushes?fromchange=d313a202a85e&full=1"
  404
  "hidden revision 'd313a202a85e'"

FIXME Specifying a tochange with a hidden changeset works

  $ httpjson "http://localhost:$HGPORT/json-pushes?startID=1&tochange=ae13d9da6966"
  404
  "hidden revision 'ae13d9da6966'"

  $ httpjson "http://localhost:$HGPORT/json-pushes?startID=1&tochange=ae13d9da6966&full=1"
  404
  "hidden revision 'ae13d9da6966'"

FIXME Specifying a hidden changeset works

  $ httpjson "http://localhost:$HGPORT/json-pushes?changeset=ae13d9da6966"
  404
  "hidden revision 'ae13d9da6966'"

  $ httpjson "http://localhost:$HGPORT/json-pushes?changeset=ae13d9da6966&full=1"
  404
  "hidden revision 'ae13d9da6966'"
