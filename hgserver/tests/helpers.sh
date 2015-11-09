# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Server-side hook enforces requirement that users have name and email
# address. Mercurial's test harness doesn't pass by default.
export HGUSER='Test User <someone@example.com>'

alias hgmo='$TESTDIR/hgmo'
alias http=$TESTDIR/testing/http-request.py

hgmoenv() {
  export DOCKER_STATE_FILE=`pwd`/.dockerstate
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

  hgmo exec hgssh /opt/kafka/bin/kafka-topics.sh --create --topic pushdata --zookeeper ${ZOOKEEPER_CONNECT} --partitions 1 --replication-factor 3 --config min.insync.replicas=2 --config unclean.leader.election.enable=false --config max.message.bytes=104857600 > /dev/null
  hgmo exec hgssh /opt/kafka/bin/kafka-topics.sh --create --topic pushlog --zookeeper ${ZOOKEEPER_CONNECT} --partitions 1 --replication-factor 3 --config min.insync.replicas=2 --config unclean.leader.election.enable=false --config max.message.bytes=104857600 > /dev/null
}

standarduser() {
  hgmo create-ldap-user user@example.com testuser 1500 'Test User' --key-file testuser --scm-level 1
  cat >> $HGRCPATH << EOF
[ui]
ssh = ssh -F `pwd`/ssh_config -i `pwd`/testuser -l user@example.com
EOF
}

alias standarduserssh='ssh -F ssh_config -i testuser -l user@example.com -p $HGPORT'
