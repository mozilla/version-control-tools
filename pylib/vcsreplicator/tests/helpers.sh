# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

. $TESTDIR/hgserver/tests/helpers.sh

vcsrenv() {
  hgmoenv

  cat >> vcsreplicator.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = pull0
topic = pushdata
group = ttest

[path_rewrites]
{moz} = $TESTTMP/repos

[pull_url_rewrites]
{moz} = ssh://${SSH_SERVER}:${SSH_PORT}
EOF

  cat >> pushdataaggregator-consumer.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = pushdataaggregatorlocal
topic = replicatedpushdata
group = pushdataaggregatorlocal
EOF

  cat >> pushdataaggregator-pendingconsumer.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = pushdataaggregatorlocal
topic = replicatedpushdatapending
group = pushdataaggregatorlocal
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

cat >> sns-consumer.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = snsnotifier-local
topic = replicatedpushdata
group = snsnotifier
EOF

}

alias consumer='vcsreplicator-consumer $TESTTMP/vcsreplicator.ini'
alias papendingconsumer='vcsreplicator-consumer $TESTTMP/pushdataaggregator-pendingconsumer.ini'
alias paconsumer='vcsreplicator-consumer $TESTTMP/pushdataaggregator-consumer.ini'
alias pulseconsumer='vcsreplicator-consumer $TESTTMP/pulse-consumer.ini'
alias snsconsumer='vcsreplicator-consumer $TESTTMP/sns-consumer.ini'
