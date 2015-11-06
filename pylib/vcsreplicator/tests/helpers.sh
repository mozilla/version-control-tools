# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

. $TESTDIR/hgserver/tests/helpers.sh

vcsrenv() {
  hgmoenv
  hgmo exec hgssh /activate-vcsreplicator --global > /dev/null
}
