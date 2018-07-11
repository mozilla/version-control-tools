configurepushlog () {
  cat >> $1/.hg/hgrc << EOF
[extensions]
pushlog = $TESTDIR/hgext/pushlog
blackbox =

[blackbox]
track = pushlog

EOF

}

dumppushlog () {
  $TESTDIR/hghooks/tests/dumppushlog.py $TESTTMP/$1
}

configurehooks () {
  cat >> $1/.hg/hgrc << EOF
[extensions]
blackbox =
# Included so mozilla.firefox_releasing config option is registered.
firefoxreleases = $TESTDIR/hgext/firefoxreleases
mozhooks = $TESTDIR/hghooks/mozhghooks/extension.py

[blackbox]
track = *

[mozilla]
repo_root = $TESTTMP
EOF
}
