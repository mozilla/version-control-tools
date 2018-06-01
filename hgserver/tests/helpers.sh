# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Server-side hook enforces requirement that users have name and email
# address. Mercurial's test harness doesn't pass by default.
export HGUSER='Test User <someone@example.com>'

alias hgmo='$TESTDIR/hgmo'
alias http=$TESTDIR/testing/http-request.py
alias pulse='$TESTDIR/pulse'

hgmoenv() {
  export DOCKER_STATE_FILE=`pwd`/.dockerstate
  export HGMO_STATE_FILE=`pwd`/hgmo.json

  hgmo start --master-ssh-port $HGPORT > /dev/null
  if [ $? -ne 0 ]; then
    exit 80
  fi
  $(hgmo shellinit)

  cat > ssh-known-hosts << EOF
${SSH_SERVER} ssh-rsa ${SSH_HOST_RSA_KEY}
${SSH_SERVER} ssh-ed25519 ${SSH_HOST_ED25519_KEY}
EOF

  cat > ssh_config << EOF
Host *
  StrictHostKeyChecking no
  PasswordAuthentication no
  PreferredAuthentications publickey
  UserKnownHostsFile `pwd`/ssh-known-hosts
  ForwardX11 no
EOF

  cat >> pulse-consumer.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = pulsenotifier-local
topic = replicatedpushdata
group = pulsenotifier
EOF

}

standarduser() {
  hgmo create-ldap-user user@example.com testuser 1500 'Test User' --key-file testuser --scm-level 1
  cat >> $HGRCPATH << EOF
[ui]
ssh = ssh -F `pwd`/ssh_config -i `pwd`/testuser -l user@example.com
EOF
}

scm3user() {
  hgmo create-ldap-user l3user@example.com l3user 3500 'L3 User' --key-file l3user --scm-level 3
  cat >> $HGRCPATH << EOF
[ui]
ssh = ssh -F `pwd`/ssh_config -i `pwd`/l3user -l l3user@example.com
EOF
}

alias standarduserssh='ssh -F ssh_config -i testuser -l user@example.com -p $HGPORT'
alias pulseconsumer='vcsreplicator-consumer $TESTTMP/pulse-consumer.ini'
