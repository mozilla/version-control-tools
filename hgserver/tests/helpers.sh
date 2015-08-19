# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

alias hgmo='$TESTDIR/hgmo'
alias http=$TESTDIR/testing/http-request.py

hgmoenv() {
  export DOCKER_STATE_FILE=`pwd`/docker-state.json
  export HGMO_STATE_FILE=`pwd`/hgmo.json

  hgmo start --master-ssh-port $HGPORT > /dev/null
  if [ $? -ne 0 ]; then
    exit 80
  fi
  $(hgmo shellinit)

  cat > ssh-known-hosts << EOF
${SSH_SERVER} ssh-rsa ${SSH_HOST_KEY}
EOF

  cat > ssh_config << EOF
Host *
  StrictHostKeyChecking no
  PasswordAuthentication no
  PreferredAuthentications publickey
  UserKnownHostsFile `pwd`/ssh-known-hosts
  ForwardX11 no
EOF
}
