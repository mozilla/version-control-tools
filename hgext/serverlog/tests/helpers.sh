localext() {
   cat >> $HGRCPATH << EOF
[extensions]
blackbox =
serverlog = $TESTDIR/hgext/serverlog

[blackbox]
track = hgweb

[serverlog]
syslog = false

[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"
EOF
}
