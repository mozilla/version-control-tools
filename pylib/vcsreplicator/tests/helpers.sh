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

}

alias consumer='vcsreplicator-consumer $TESTTMP/vcsreplicator.ini'
alias paconsumer='vcsreplicator-consumer $TESTTMP/pushdataaggregator-consumer.ini'
