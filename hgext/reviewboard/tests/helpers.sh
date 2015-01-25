repoconfig() {
  cat >> $1 << EOF
[reviewboard]
repoid = 1
EOF
}

clientconfig() {
  cat >> $1 << EOF
[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"

[mozilla]
ircnick = mynick

[paths]
default-push = ssh://user@dummy/$TESTTMP/repos/test-repo

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

alias rbmanage='$TESTDIR/reviewboard'
alias bugzilla='$TESTDIR/bugzilla'
alias dockercontrol='$TESTDIR/testing/docker-control.py'
alias pulse='$TESTDIR/pulse'

commonenv() {
  $TESTDIR/testing/docker-control.py start-bmo $1 $HGPORT2 --pulse-port $HGPORT3 > /dev/null
  export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT2
  export PULSE_HOST=${DOCKER_HOSTNAME}
  export PULSE_PORT=${HGPORT3}

  mkdir repos
  cat >> repos/hgrc << EOF
[phases]
publish = False

[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"

[reviewboard]
url = http://localhost:$HGPORT1/

[extensions]
reviewboard = $TESTDIR/hgext/reviewboard/server.py

[bugzilla]
url = ${BUGZILLA_URL}
EOF

  export HGSSHHGRCPATH=`pwd`/repos/hgrc

  cat >> repos/web.conf << EOF
[web]
push_ssl = False
allow_push = *

[paths]
/ = `pwd`/repos/**
EOF

  hg init client
  hg init repos/test-repo
  rbmanage create rbserver
  rbmanage repo rbserver test-repo http://localhost:$HGPORT/test-repo
  rbmanage start rbserver $HGPORT1
  repoconfig repos/test-repo/.hg/hgrc
  clientconfig client/.hg/hgrc

  HGRCPATH=`pwd`/repos/hgrc hg serve -d -p $HGPORT --pid-file hg.pid --web-conf repos/web.conf --accesslog hg.access.log --errorlog hg.error.log
  cat hg.pid >> $DAEMON_PIDS

  pulse create-queue exchange/mozreview/ all
}

exportbzauth() {
  export BUGZILLA_USERNAME=$1
  export BUGZILLA_PASSWORD=$2
}
