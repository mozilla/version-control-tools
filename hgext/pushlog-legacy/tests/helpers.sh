serverconfig() {
  cat >> $1 << EOF
[extensions]
pushlog-feed = $TESTDIR/hgext/pushlog-legacy/pushlog-feed.py
buglink = $TESTDIR/hgext/pushlog-legacy/buglink.py
hgwebjson = $TESTDIR/hgext/pushlog-legacy/hgwebjson.py
pushlog = $TESTDIR/hgext/pushlog

[web]
push_ssl = False
allow_push = *
templates = $TESTDIR/hgtemplates
style = gitweb_mozilla

[hooks]
pretxnchangegroup.pushlog = python:mozhghooks.pushlog.log

EOF
}

alias http=$TESTDIR/testing/http-request.py

jsoncompare() {
  python $TESTDIR/hgext/pushlog-legacy/tests/json-compare.py $1 $2
}
