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

[bugzilla]
username = ${BUGZILLA_USERNAME}
password = ${BUGZILLA_PASSWORD}

# We want [extensions] to be last because some tests write
# ext=path/to/ext lines.

[extensions]
strip =
rebase =
reviewboard = $TESTDIR/hgext/reviewboard/client.py
EOF

}

alias rbmanage='$TESTDIR/reviewboard'
alias bugzilla='$TESTDIR/bugzilla'
alias adminbugzilla='BUGZILLA_USERNAME=admin@example.com BUGZILLA_PASSWORD=password $TESTDIR/bugzilla'
alias dockercontrol='$TESTDIR/testing/docker-control.py'
alias pulse='$TESTDIR/pulse'
alias mozreview='$TESTDIR/mozreview'
alias ottoland='$TESTDIR/ottoland'

commonenv() {
  mozreview start `pwd` --mercurial-port $HGPORT --reviewboard-port $HGPORT1 --bugzilla-port $HGPORT2 --pulse-port $HGPORT3 --autoland-port $HGPORT4 > /dev/null
  export MOZREVIEW_HOME=`pwd`
  export HGSSHHGRCPATH=${MOZREVIEW_HOME}/hgrc

  mozreview create-repo test-repo > /dev/null

  export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT2
  export REVIEWBOARD_URL=http://localhost:$HGPORT1/
  export PULSE_HOST=${DOCKER_HOSTNAME}
  export PULSE_PORT=${HGPORT3}
  export AUTOLAND_URL=http://${DOCKER_HOSTNAME}:${HGPORT4}/

  hg init client
  clientconfig client/.hg/hgrc

  pulse create-queue exchange/mozreview/ all
}

exportbzauth() {
  export BUGZILLA_USERNAME=$1
  export BUGZILLA_PASSWORD=$2
}
