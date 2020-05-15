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

ppjson_params=$(python -c 'from __future__ import print_function; from sys import version_info as v; print("--sort-keys") if v.major == 3 and v.minor >= 5 else print("")')
alias ppjson="python -m json.tool $ppjson_params"

