repoconfig() {
  cat >> $1 << EOF
[reviewboard]
repoid = 1
username=mozreview
password=password
EOF
}

clientconfig() {
  cat >> $1 << EOF
[ui]
ssh = $TESTDIR/testing/mozreview-ssh

[mozilla]
ircnick = mynick

[paths]
default-push = ssh://${HGSSH_HOST}:${HGSSH_PORT}/test-repo

# We want [extensions] to be last because some tests write
# ext=path/to/ext lines.

# Make generated IDs deterministic.
[reviewboard]
fakeids = true

[extensions]
strip =
rebase =
reviewboard = $TESTDIR/hgext/reviewboard/client.py

EOF

  # Put Bugzilla credentials in global hgrc because not all parts of hg
  # (like password manager) load config options from the repo hgrc.
  cat >> $HGRCPATH << EOF
[bugzilla]
username = ${BUGZILLA_USERNAME}
apikey = $2
EOF

}

alias adminbugzilla='BUGZILLA_USERNAME=admin@example.com BUGZILLA_PASSWORD=password $TESTDIR/bugzilla'
alias bugzilla='$TESTDIR/bugzilla'
alias pulse='$TESTDIR/pulse'
alias mozreview='$TESTDIR/mozreview'
alias ottoland='$TESTDIR/ottoland'
alias treestatus='$TESTDIR/treestatus'
alias rbmanage='$TESTDIR/reviewboard'
alias http='$TESTDIR/testing/http-request.py'

commonenv() {
  mozreview start `pwd` \
    --mercurial-port $HGPORT \
    --reviewboard-port $HGPORT1 \
    --bugzilla-port $HGPORT2 \
    --pulse-port $HGPORT3 \
    --autoland-port $HGPORT4 \
    --ldap-port $HGPORT5 \
    --ssh-port $HGPORT6 \
    --hgweb-port $HGPORT7 \
    --treestatus-port $HGPORT8 \
    > /dev/null

  # MozReview randomly fails to start. Handle it elegantly.
  if [ $? -ne 0 ]; then
    exit 80
  fi

  $(mozreview shellinit `pwd`)

  export HGSSHHGRCPATH=${MOZREVIEW_HOME}/hgrc

  mozreview create-user default@example.com password 'Default User' \
    --bugzilla-group editbugs \
    --uid 2000 \
    --scm-level 1 > /dev/null

  apikey=`mozreview create-api-key default@example.com`

  exportbzauth default@example.com password

  mozreview create-repo test-repo > /dev/null

  hg init client
  clientconfig client/.hg/hgrc ${apikey}

  pulse create-queue exchange/mozreview/ all
}

exportbzauth() {
  export BUGZILLA_USERNAME=$1
  export BUGZILLA_PASSWORD=$2
}
