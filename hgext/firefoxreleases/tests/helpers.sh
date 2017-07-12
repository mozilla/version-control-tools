enable_extension() {
  cat >> $HGRCPATH << EOF
[extensions]
firefoxreleases = $TESTDIR/hgext/firefoxreleases
EOF
}

populate_simple_repo() {
  touch foo
  hg -q commit -A -m initial
  echo 1 > foo
  hg commit -m 'commit 1'
  echo 2 > foo
  hg commit -m 'commit 2'
  echo 3 > foo
  hg commit -m 'commit 3'
}

populate_simple_releases() {
  $TESTDIR/scripts/firefox-releases import-serialized-builds .hg/firefoxreleases.db << EOF
{"_format": 1, "app_version": "55.0a1", "artifacts_url": "https://example.com/build0/", "build_id": "20170526000000", "channel": "nightly", "day": 1495756800, "insertion_key": 1, "platform": "win32", "revision": "94086d65796fd7fc8f957a2c5548db17a13f1f1f"}
{"_format": 1, "app_version": "56.0a1", "artifacts_url": "https://example.com/build1/", "build_id": "20170527000000", "channel": "nightly", "day": 1495843200, "insertion_key": 1, "platform": "win64", "revision": "dc94f7af4edae241d4382901b48cb67e43c445e1"}
{"_format": 1, "app_version": "57.0a1", "artifacts_url": "https://example.com/build2/", "build_id": "20170527000000", "channel": "nightly", "day": 1495843200, "insertion_key": 1, "platform": "linux64", "revision": "4e0f86874d2556a19bcb5b6d090d24a720229178"}
EOF
}

start_server() {
  hg init server
  cd server
  populate_simple_repo
  populate_simple_releases > /dev/null

  cat > .hg/hgrc << EOF
[extensions]
hgmo = $TESTDIR/hgext/hgmo

[mozilla]
enablefirefoxreleases = true
EOF

  touch .hg/IS_FIREFOX_REPO

  hg serve -d -p $HGPORT --pid-file hg.pid --hgmo
  cat hg.pid >> $DAEMON_PIDS
  cd ..
}

alias http=$TESTDIR/testing/http-request.py
