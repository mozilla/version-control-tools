startserver() {
  hg init server
  cd server
  cat > .hg/hgrc << EOF
[extensions]
clonebundles =
hgmo = $TESTDIR/hgext/hgmo

[web]
push_ssl = False
allow_push = *
EOF

  hg serve -d -p $HGPORT --pid-file hg.pid --hgmo -E error.log
  cat hg.pid >> $DAEMON_PIDS
  cd ..
}

alias http=$TESTDIR/testing/http-request.py
