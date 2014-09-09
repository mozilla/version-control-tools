configurepushlog () {
  cat >> $1/.hg/hgrc << EOF
[extensions]
pushlog = $TESTDIR/hgext/pushlog

[hooks]
pretxnchangegroup.pushlog = python:mozhghooks.pushlog.log
EOF

}

dumppushlog () {
  $TESTDIR/hghooks/tests/dumppushlog.py $TESTTMP/$1
}
