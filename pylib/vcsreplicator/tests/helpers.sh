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

cat >> sns-consumer.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = snsnotifier-local
topic = replicatedpushdata
group = snsnotifier
EOF

cat >> filtered-consumer.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = filteredconsumer-local
topic = pushdata
group = filteredconsumer
[replicationrules]
include.projects = re:\{moz\}/projects/.*
include.central = path:{moz}/mozilla-central
exclude.unified = path:{moz}/mozilla-unified
exclude.users = re:\{moz\}/users/.*
EOF

cat >> filtered-consumer-default.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
poll_timeout = 0.2
client_id = filteredconsumerdefault-local
topic = pushdata
group = filteredconsumerdefault
[replicationrules]
exclude.ash = path:{moz}/projects/ash
include.all = re:\{moz\}/.*
EOF
}

alias consumer='vcsreplicator-consumer $TESTTMP/vcsreplicator.ini'
alias papendingconsumer='vcsreplicator-consumer $TESTTMP/pushdataaggregator-pendingconsumer.ini'
alias paconsumer='vcsreplicator-consumer $TESTTMP/pushdataaggregator-consumer.ini'
alias pulseconsumer='vcsreplicator-consumer $TESTTMP/pulse-consumer.ini'
alias snsconsumer='vcsreplicator-consumer $TESTTMP/sns-consumer.ini'
alias filteredconsumer='vcsreplicator-consumer $TESTTMP/filtered-consumer.ini'
alias filteredconsumerdefault='vcsreplicator-consumer $TESTTMP/filtered-consumer-default.ini'
