serverconfig() {
  cat >> $1 << EOF
[phases]
publish = False

[web]
push_ssl = False
allow_push = *

[reviewboard]
url = http://dummy
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
username = user
password = pass

[extensions]
reviewboard = $TESTDIR/hgext/reviewboard/client.py

EOF
}

removeserverstate() {
  rm $1/.hg/DUMMY_REVIEWS
  rm $1/.hg/post_reviews

}
