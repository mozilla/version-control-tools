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

[mozilla]
ircnick = mynick

[paths]
default-push = ssh://user@dummy/$TESTTMP/server

EOF

if [ -z ${NO_BUGZILLA_AUTH} ]; then
  cat >> $1 << EOF
[bugzilla]
username = ${BUGZILLA_USERNAME}
password = ${BUGZILLA_PASSWORD}
EOF

  # We want [extensions] to be last because some tests write
  # ext=path/to/ext lines.
  cat >> $1 << EOF

[extensions]
strip =
rebase =
reviewboard = $TESTDIR/hgext/reviewboard/client.py

EOF

fi

}

alias rbmanage='python $TESTDIR/hgext/reviewboard/tests/rbmanage.py'
alias bugzilla='$TESTDIR/testing/bugzilla.py'
alias dockercontrol='$TESTDIR/testing/docker-control.py'

commonenv() {
  $TESTDIR/testing/docker-control.py start-bmo $1 $HGPORT2 > /dev/null
  export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT2
  $TESTDIR/testing/bugzilla.py create-group reviewboard 'reviewboard users'

  hg init client
  hg init server
  rbmanage create rbserver
  rbmanage repo rbserver test-repo http://localhost:$HGPORT/
  rbmanage start rbserver $HGPORT1
  serverconfig server/.hg/hgrc $HGPORT1
  clientconfig client/.hg/hgrc
  hg serve -R server -d -p $HGPORT --pid-file hg.pid
  cat hg.pid >> $DAEMON_PIDS
}

exportbzauth() {
  export BUGZILLA_USERNAME=$1
  export BUGZILLA_PASSWORD=$2
}
