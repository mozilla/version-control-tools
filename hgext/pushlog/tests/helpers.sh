serverconfig() {
  cat >> $1 << EOF
[extensions]
hgmo = $TESTDIR/hgext/hgmo
pushlog-feed = $TESTDIR/hgext/pushlog/feed.py
pushlog = $TESTDIR/hgext/pushlog

[web]
push_ssl = False
allow_push = *
templates = $TESTDIR/hgtemplates
style = gitweb_mozilla

[hooks]
pretxnchangegroup.pushlog = python:mozhghooks.pushlog.log

EOF
}

alias http=$TESTDIR/testing/http-request.py

jsoncompare() {
  python $TESTDIR/hgext/pushlog/tests/json-compare.py $1 $2
}

httpjson() {
  http --body-file body --no-headers $1
  python -m json.tool < body
}

wsgiconfig() {
  cat >> $1 << EOF
[paths]
/ = /$TESTTMP/*

EOF
}

maketestrepousers() {
  hg init hg-test
  cd hg-test
  serverconfig .hg/hgrc
  wsgiconfig config.wsgi
  hg serve -d -p $HGPORT --pid-file hg.pid -E error.log --web-conf config.wsgi
  cat hg.pid >> $DAEMON_PIDS

  cd ..

  hg clone http://localhost:$HGPORT/hg-test client > /dev/null
  cd client

  touch testfile

  export STARTTIME="2008-11-20%2010:50:00"

  # Push 1
  echo "checkin 1" >> testfile
  hg commit -A -m "checkin 1" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227282600, user = "luser" WHERE id = 1'

  # Push 2
  echo "checkin 2" >> testfile
  hg commit -A -m "checkin 2" --user "luser"
  echo "checkin 3" >> testfile
  hg commit -A -m "checkin 3" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227369000, user = "luser" WHERE id = 2'

  # Push 3
  echo "checkin 4" >> testfile
  hg commit -A -m "checkin 4" --user "someone@cuatro"
  echo "checkin 5" >> testfile
  hg commit -A -m "checkin 5" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227455400, user = "someone" WHERE id = 3'

  # Push 4
  echo "checkin 6" >> testfile
  hg commit -A -m "checkin 6" --user "johndoe@cuatro"
  echo "checkin 7" >> testfile
  hg commit -A -m "checkin 7" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227541800, user = "johndoe" WHERE id = 4'

  # Get the time after a few pushes,
  # so we can test filtering and
  # have less output in tests
  export MIDTIME="2008-11-25%2010:50:00"

  # Push 5
  echo "checkin 8" >> testfile
  hg commit -A -m "checkin 8" --user "luser"
  echo "checkin 9" >> testfile
  hg commit -A -m "checkin 9" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227714600, user = "luser" WHERE id = 5'

  # Push 6
  echo "checkin 10" >> testfile
  hg commit -A -m "checkin 10" --user "someone@cuatro"
  echo "checkin 11" >> testfile
  hg commit -A -m "checkin 11" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227801000, user = "someone" WHERE id = 6'
  
  # Push 7
  echo "checkin 12" >> testfile
  hg commit -A -m "checkin 12" --user "johndoe@cuatro"
  echo "checkin 13" >> testfile
  hg commit -A -m "checkin 13" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227887400, user = "johndoe" WHERE id = 7'
  
  # Push 8
  echo "checkin 14" >> testfile
  hg commit -A -m "checkin 14" --user "luser"
  echo "checkin 15" >> testfile
  hg commit -A -m "checkin 15" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1227973800, user = "luser" WHERE id = 8'
  
  # Push 9
  echo "checkin 16" >> testfile
  hg commit -A -m "checkin 16" --user "someone@cuatro"
  echo "checkin 17" >> testfile
  hg commit -A -m "checkin 17" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228060200, user = "someone" WHERE id = 9'
  
  # Push 10
  echo "checkin 18" >> testfile
  hg commit -A -m "checkin 18" --user "johndoe@cuatro"
  echo "checkin 19" >> testfile
  hg commit -A -m "checkin 19" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228146600, user = "johndoe" WHERE id = 10'
  
  # Push 11
  echo "checkin 20" >> testfile
  hg commit -A -m "checkin 20" --user "luser"
  echo "checkin 21" >> testfile
  hg commit -A -m "checkin 21" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228233000, user = "luser" WHERE id = 11'
  
  # Push 12
  echo "checkin 22" >> testfile
  hg commit -A -m "checkin 22" --user "someone@cuatro"
  echo "checkin 23" >> testfile
  hg commit -A -m "checkin 23" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228319400, user = "someone" WHERE id = 12'
  
  # Push 13
  echo "checkin 24" >> testfile
  hg commit -A -m "checkin 24" --user "johndoe@cuatro"
  echo "checkin 25" >> testfile
  hg commit -A -m "checkin 25" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228405800, user = "johndoe" WHERE id = 13'
  
  # Push 14
  echo "checkin 26" >> testfile
  hg commit -A -m "checkin 26" --user "luser"
  echo "checkin 27" >> testfile
  hg commit -A -m "checkin 27" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228492200, user = "luser" WHERE id = 14'
  
  # Push 15
  echo "checkin 28" >> testfile
  hg commit -A -m "checkin 28" --user "someone@cuatro"
  echo "checkin 29" >> testfile
  hg commit -A -m "checkin 29" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228578600, user = "someone" WHERE id = 15'
  
  # Push 16
  echo "checkin 30" >> testfile
  hg commit -A -m "checkin 30" --user "johndoe@cuatro"
  echo "checkin 31" >> testfile
  hg commit -A -m "checkin 31" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228751400, user = "johndoe" WHERE id = 16'
  
  # Push 17
  echo "checkin 32" >> testfile
  hg commit -A -m "checkin 32" --user "luser"
  echo "checkin 33" >> testfile
  hg commit -A -m "checkin 33" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228837800, user = "luser" WHERE id = 17'
  
  # Push 18
  echo "checkin 34" >> testfile8
  hg commit -A -m "checkin 34" --user "someone@cuatro"
  echo "checkin 35" >> testfile
  hg commit -A -m "checkin 35" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1228924200, user = "someone" WHERE id = 18'
  
  # Push 19
  echo "checkin 36" >> testfile
  hg commit -A -m "checkin 36" --user "johndoe@cuatro"
  echo "checkin 37" >> testfile
  hg commit -A -m "checkin 37" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229010600, user = "johndoe" WHERE id = 19'
  
  # Push 20
  echo "checkin 38" >> testfile
  hg commit -A -m "checkin 38" --user "luser"
  echo "checkin 39" >> testfile
  hg commit -A -m "checkin 39" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229097000, user = "luser" WHERE id = 20'
  
  # Push 21
  echo "checkin 40" >> testfile
  hg commit -A -m "checkin 40" --user "someone@cuatro"
  echo "checkin 41" >> testfile
  hg commit -A -m "checkin 41" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229140200, user = "someone" WHERE id = 21'
  
  # Push 22
  echo "checkin 42" >> testfile
  hg commit -A -m "checkin 42" --user "johndoe@cuatro"
  echo "checkin 43" >> testfile
  hg commit -A -m "checkin 43" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229183400, user = "johndoe" WHERE id = 22'
  
  # Push 23
  echo "checkin 44" >> testfile
  hg commit -A -m "checkin 44" --user "luser"
  echo "checkin 45" >> testfile
  hg commit -A -m "checkin 45" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229269800, user = "luser" WHERE id = 23'
  
  # Push 24
  echo "checkin 46" >> testfile
  hg commit -A -m "checkin 46" --user "someone@cuatro"
  echo "checkin 47" >> testfile
  hg commit -A -m "checkin 47" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229356200, user = "someone" WHERE id = 24'
  
  # Push 25
  echo "checkin 48" >> testfile
  hg commit -A -m "checkin 48" --user "johndoe@cuatro"
  echo "checkin 49" >> testfile
  hg commit -A -m "checkin 49" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229442600, user = "johndoe" WHERE id = 25'
  
  # Push 26
  echo "checkin 50" >> testfile
  hg commit -A -m "checkin 50" --user "luser"
  echo "checkin 51" >> testfile
  hg commit -A -m "checkin 51" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229529000, user = "luser" WHERE id = 26'
  
  # Push 27
  echo "checkin 52" >> testfile
  hg commit -A -m "checkin 52" --user "someone@cuatro"
  echo "checkin 53" >> testfile
  hg commit -A -m "checkin 53" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229615400, user = "someone" WHERE id = 27'
  
  # Push 28
  echo "checkin 54" >> testfile
  hg commit -A -m "checkin 54" --user "johndoe@cuatro"
  echo "checkin 55" >> testfile
  hg commit -A -m "checkin 55" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229701800, user = "johndoe" WHERE id = 28'
  
  # Push 29
  echo "checkin 56" >> testfile
  hg commit -A -m "checkin 56" --user "luser"
  echo "checkin 57" >> testfile
  hg commit -A -m "checkin 57" --user "luser"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229788200, user = "luser" WHERE id = 29'
  
  # Push 30
  echo "checkin 58" >> testfile
  hg commit -A -m "checkin 58" --user "someone@cuatro"
  echo "checkin 59" >> testfile
  hg commit -A -m "checkin 59" --user "someone@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229874600, user = "someone" WHERE id = 30'
  
  # Push 31
  echo "checkin 60" >> testfile
  hg commit -A -m "checkin 60" --user "johndoe@cuatro"
  echo "checkin 61" >> testfile
  hg commit -A -m "checkin 61" --user "johndoe@cuatro"
  hg push
  sqlite3 ../hg-test/.hg/pushlog2.db 'UPDATE pushlog SET date = 1229961000, user = "johndoe" WHERE id = 31'
  
  export ENDTIME="2008-12-23%2010:50:00"
}
