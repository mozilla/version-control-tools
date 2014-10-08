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
  username=testadmin
  password=password
  if [ ! -z ${USE_BZ_AUTH} ]; then
    username=${BUGZILLA_USERNAME}
    password=${BUGZILLA_PASSWORD}
  fi

  cat >> $1 << EOF
[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"

[bugzilla]
username = ${username}
password = ${password}

[mozilla]
ircnick = mynick

[paths]
default-push = ssh://user@dummy/$TESTTMP/server

[extensions]
strip =
rebase =
reviewboard = $TESTDIR/hgext/reviewboard/client.py

EOF
}

rbmanage() {
  python $TESTDIR/hgext/reviewboard/tests/rbmanage.py $1 $2 $3 $4 $5
}

bugzilla() {
  $TESTDIR/testing/bugzilla.py $1 $2 $3 $4 $5 $6 $7 $8 $9
}

dockercontrol() {
  $TESTDIR/testing/docker-control.py $1 $2 $3 $4 $5
}

commonenv() {
  $TESTDIR/testing/docker-control.py start-bmo $1 $HGPORT2 > /dev/null
  export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$HGPORT2
  $TESTDIR/testing/bugzilla.py create-group reviewboard 'reviewboard users'
  export USE_BZ_AUTH=1

  hg init client
  hg init server
  rbmanage rbserver create
  rbmanage rbserver repo test-repo http://localhost:$HGPORT/
  rbmanage rbserver start $HGPORT1
  serverconfig server/.hg/hgrc $HGPORT1
  clientconfig client/.hg/hgrc
  hg serve -R server -d -p $HGPORT --pid-file hg.pid
  cat hg.pid >> $DAEMON_PIDS
}
