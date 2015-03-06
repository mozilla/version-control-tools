configurebzexport() {
  USERNAME=$3
  if [ -z $USERNAME ]; then
    USERNAME=admin@example.com
  fi
  PASSWORD=$4
  if [ -z $PASSWORD ]; then
    PASSWORD=password
  fi

  export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$1

  cat >> $2 << EOF
[extensions]
mq =
bzexport = $TESTDIR/hgext/bzexport

[bzexport]
bugzilla = ${BUGZILLA_URL}/

[bugzilla]
username = ${USERNAME}
password = ${PASSWORD}
EOF
}

alias bugzilla=$TESTDIR/bugzilla
alias adminbugzilla='BUGZILLA_USERNAME=admin@example.com BUGZILLA_PASSWORD=password $TESTDIR/bugzilla'
