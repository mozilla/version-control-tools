alias hgmo='$TESTDIR/hgmo'
alias testssh='ssh -T -F ssh_config'

hgmoenv() {
  export DOCKER_STATE_FILE=`pwd`/docker-state.json
  export HGMO_STATE_FILE=`pwd`/hgmo.json

  hgmo start --master-ssh-port $HGPORT > /dev/null
  export SSH_SERVER=${DOCKER_HOSTNAME}

  cat > ssh_config << EOF
Host *
  StrictHostKeyChecking no
  PasswordAuthentication no
  PreferredAuthentications publickey
  UserKnownHostsFile `pwd`/ssh-known-hosts
  ForwardX11 no
EOF
}

alias testuserssh='ssh -F ssh_config -i testuser -l user@example.com -p $HGPORT'

standarduser() {
  hgmo create-ldap-user user@example.com testuser 1500 'Test User' --key-file testuser --scm-level 1
  cat >> $HGRCPATH << EOF
[ui]
ssh = ssh -F `pwd`/ssh_config -i `pwd`/testuser -l user@example.com
EOF
}

cleanup() {
  hgmo aggregate-code-coverage $TESTDIR/coverage
  hgmo clean
}
