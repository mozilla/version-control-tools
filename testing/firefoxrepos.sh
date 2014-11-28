# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

makefirefoxrepo() {
  if [ ! -d $1 ]; then
    hg init $1
    touch $1/.hg/IS_FIREFOX_REPO
  fi
}

# Construct a tree of repositories mimicking hg.mozilla.org.
makefirefoxrepos() {
  makefirefoxrepo $1/mozilla-central
  makefirefoxrepo $1/try
  makefirefoxrepo $1/releases/mozilla-aurora
  makefirefoxrepo $1/releases/mozilla-beta
  makefirefoxrepo $1/releases/mozilla-release
  makefirefoxrepo $1/releases/mozilla-esr31
  makefirefoxrepo $1/integration/mozilla-inbound
  makefirefoxrepo $1/integration/fx-team
  makefirefoxrepo $1/projects/alder
  makefirefoxrepo $1/unified
}

# Make Firefox repositories and start a server.
makefirefoxreposserver() {
  makefirefoxrepos $1
  root=`pwd`/$1
  cat > hgweb.conf << EOF
[paths]
/ = $root/*
EOF

  if [ ! -z "${PUSHABLE_HTTP}" ]; then
    cat >> hgweb.conf << EOF
[web]
push_ssl = False
allow_push = *
EOF
  fi

  hg serve -d -p $2 --pid-file hg.pid --web-conf hgweb.conf
  cat hg.pid >> $DAEMON_PIDS
}

# Hack up hgrc to point against a local server.
installfakereposerver() {
  cat >> $HGRCPATH << EOF
[extensions]
localmozrepo = $TESTDIR/testing/local-mozilla-repos.py

[ui]
ssh = python "$TESTDIR/pylib/mercurial-support/dummyssh"

[localmozrepo]
readuri = http://localhost:$1/
writeuri = ssh://user@dummy/$2/
EOF
}

populatedummydata() {
  oldpwd=`pwd`
  cd $1/mozilla-central
  touch foo
  hg commit -A -m 'Bug 456 - initial commit to m-c; r=gps'

  echo 'foo2' > foo
  hg commit -m 'Bug 457 - second commit to m-c; r=ted'

  cd ../integration/mozilla-inbound
  hg pull ../../mozilla-central
  hg up tip
  echo 'inbound1' > foo
  hg commit -m 'Bug 458 - Commit to inbound'
  echo 'inbound2' > foo
  hg commit -m 'Bug 459 - Second commit to inbound'
  cd ../fx-team
  hg pull ../../mozilla-central
  hg up tip
  touch bar
  hg commit -A -m 'Bug 460 - Create bar on fx-team'

  cd $oldpwd
}
