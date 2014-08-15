configurepushlog () {
  cat >> $1/.hg/hgrc << EOF
[hooks]
pretxnchangegroup.pushlog = python:mozhghooks.pushlog.log
EOF

}

dumppushlog () {
  $TESTDIR/hghooks/tests/dumppushlog.py $TESTTMP/$1
}
