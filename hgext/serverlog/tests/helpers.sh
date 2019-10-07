localext() {
   cat >> $HGRCPATH << EOF
[extensions]
blackbox =
serverlog = $TESTDIR/hgext/serverlog

[blackbox]
track = hgweb

[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
EOF
}
