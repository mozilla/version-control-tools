starthttpserver() {
  python $TESTDIR/hgext/bundleclone/tests/httpserver.py $1 2> server.log &
  # Wait for server to start to avoid race conditions.
  while [ -f listening -a ! -f errored ]; do
    sleep 0;
  done

  if [ -f errored ]; then
    echo "server failed to start!"
    exit 1
  fi
}
