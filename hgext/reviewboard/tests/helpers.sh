serverconfig() {
  cat >> $1 << EOF
[phases]
publish = False

[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"

[web]
push_ssl = False
allow_push = *

[reviewboard]
url = http://localhost:$2
repoid = 1

[extensions]
reviewboard = $TESTDIR/hgext/reviewboard/server.py

EOF
}

clientconfig() {
  cat >> $1 << EOF
[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"

[bugzilla]
username = testadmin
password = password

[extensions]
reviewboard = $TESTDIR/hgext/reviewboard/client.py

EOF
}

rbmanage() {
  python $TESTDIR/hgext/reviewboard/tests/rbmanage.py $1 $2 $3 $4 $5
}
