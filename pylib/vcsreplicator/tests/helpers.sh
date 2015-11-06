# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

. $TESTDIR/hgserver/tests/helpers.sh

vcsrenv() {
  hgmoenv
  hgmo exec hgssh /activate-vcsreplicator --global > /dev/null

  cat >> vcsreplicator.ini << EOF
[consumer]
hosts = ${KAFKA_0_HOSTPORT}, ${KAFKA_1_HOSTPORT}, ${KAFKA_2_HOSTPORT}
connect_timeout = 5
client_id = pull0
topic = pushdata
group = ttest

[path_rewrites]
{moz} = $TESTTMP/repos
EOF

}

alias consumer='python -m vcsreplicator.consumer $TESTTMP/vcsreplicator.ini'
