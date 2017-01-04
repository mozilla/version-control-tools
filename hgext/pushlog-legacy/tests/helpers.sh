serverconfig() {
  cat >> $1 << EOF
[extensions]
hgmo = $TESTDIR/hgext/hgmo
pushlog-feed = $TESTDIR/hgext/pushlog-legacy/pushlog-feed.py
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

httpjson() {
  http --body-file body --no-headers $1
  python -m json.tool < body
}
