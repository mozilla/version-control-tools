repoconfig() {
  cat >> $1 << EOF
[reviewboard]
repoid = 1
EOF
}

clientconfig() {
  cat >> $1 << EOF
[ui]
ssh = $TESTDIR/testing/mozreview-ssh

[mozilla]
ircnick = mynick

[paths]
default-push = ssh://${HGSSH_HOST}:${HGSSH_PORT}/test-repo

[bugzilla]
username = ${BUGZILLA_USERNAME}
password = ${BUGZILLA_PASSWORD}

# We want [extensions] to be last because some tests write
# ext=path/to/ext lines.

# Make generated IDs deterministic.
[reviewboard]
fakeids = true

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
  mozreview start `pwd` \
    --mercurial-port $HGPORT \
    --reviewboard-port $HGPORT1 \
    --bugzilla-port $HGPORT2 \
    --pulse-port $HGPORT3 \
    --autoland-port $HGPORT4 \
    --ldap-port $HGPORT5 \
    --ssh-port $HGPORT6 \
    > /dev/null

  # MozReview randomly fails to start. Handle it elegantly.
  if [ $? -ne 0 ]; then
    exit 80
  fi

  $(mozreview shellinit `pwd`)

  export HGSSHHGRCPATH=${MOZREVIEW_HOME}/hgrc

  createandusedefaultuser > /dev/null
  mozreview create-ldap-user default@example.com defaultuser 2000 'Default User' \
    --key-file ${MOZREVIEW_HOME}/keys/default@example.com \
    --scm-level 1

  mozreview create-repo test-repo > /dev/null

  hg init client
  clientconfig client/.hg/hgrc

  pulse create-queue exchange/mozreview/ all
}

exportbzauth() {
  export BUGZILLA_USERNAME=$1
  export BUGZILLA_PASSWORD=$2
}

createandusedefaultuser() {
  adminbugzilla create-user default@example.com password 'Default User' --group editbugs
  exportbzauth default@example.com password
}
