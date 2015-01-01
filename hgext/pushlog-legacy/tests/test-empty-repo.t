  $ . $TESTDIR/hgext/pushlog-legacy/tests/helpers.sh
  $ hg init server
  $ cd server
  $ serverconfig .hg/hgrc

  $ hg serve -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS

Accessing /pushlog on a repo without a pushlog db should succeed

  $ http http://localhost:$HGPORT/pushlog --header content-type
  200
  content-type: application/atom+xml
  
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://*:$HGPORT/pushlog</id> (glob)
   <link rel="self" href="http://*:$HGPORT/pushlog"/> (glob)
   <link rel="alternate" href="http://*:$HGPORT/pushloghtml"/> (glob)
   <title>server Pushlog</title>
   <updated>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z</updated> (re)
  
  </feed>
  

Accessing an empty repo should not have created the pushlog db

  $ ls .hg
  00changelog.i
  hgrc
  requires
  store

Accessing a read-only repository should also succeed

  $ chmod 555 .hg

  $ http http://localhost:$HGPORT/pushlog --no-body --header content-type
  200
  content-type: application/atom+xml

  $ chmod 775 .hg

Create an empty database and test variations with that

  $ hg verifypushlog
  pushlog contains all 0 changesets across 0 pushes

  $ ls .hg
  00changelog.i
  hgrc
  pushlog2.db
  requires
  store

  $ http http://localhost:$HGPORT/json-pushes --header content-type
  200
  content-type: application/json
  
  {}
