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
  UserKnownHostsFile ssh-known-hosts
  ForwardX11 no
EOF
}
