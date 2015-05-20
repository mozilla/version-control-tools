starthttpserver() {
  python $TESTDIR/hgext/bundleclone/tests/httpserver.py $1 2> server.log &
  # Wait for server to start to avoid race conditions.
  while [ -f listening ]; do
    sleep 0;
  done
}
