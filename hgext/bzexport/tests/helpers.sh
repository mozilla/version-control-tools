alias bugzilla=$TESTDIR/bugzilla
alias adminbugzilla='BUGZILLA_USERNAME=admin@example.com BUGZILLA_PASSWORD=password $TESTDIR/bugzilla'

configurebzexport() {
  export BUGZILLA_URL=http://${DOCKER_HOSTNAME}:$1

  adminbugzilla create-user default@example.com password 'Default User' --group editbugs > /dev/null

  USERNAME=default@example.com
  PASSWORD=password

  export BUGZILLA_USERNAME=default@example.com
  export BUGZILLA_PASSWORD=password

  cat >> $2 << EOF
[extensions]
mq =
bzexport = $TESTDIR/hgext/bzexport

[bzexport]
bugzilla = ${BUGZILLA_URL}/
update-patch = True
rename-patch = True

[bugzilla]
username = ${USERNAME}
password = ${PASSWORD}
EOF
}
