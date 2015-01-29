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
