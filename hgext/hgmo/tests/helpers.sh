startserver() {
  hg init server
  cd server
  cat > .hg/hgrc << EOF
[extensions]
hgmo = $TESTDIR/hgext/hgmo
pushlog = $TESTDIR/hgext/pushlog
buglink = $TESTDIR/hgext/pushlog-legacy/buglink.py
pushlog-feed = $TESTDIR/hgext/pushlog-legacy/pushlog-feed.py
hgwebjson = $TESTDIR/hgext/pushlog-legacy/hgwebjson.py

[web]
push_ssl = False
allow_push = *
templates = $TESTDIR/hgtemplates
style = gitweb_mozilla
EOF

  hg serve -d -p $HGPORT --pid-file hg.pid
  cat hg.pid >> $DAEMON_PIDS
  cd ..
}

alias http=$TESTDIR/testing/http-request.py
