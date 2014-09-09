configurepushlog () {
  cat >> $1/.hg/hgrc << EOF
[extensions]
pushlog = $TESTDIR/hgext/pushlog
EOF

}

dumppushlog () {
  $TESTDIR/hghooks/tests/dumppushlog.py $TESTTMP/$1
}
