# make git commits deterministic and environment agnostic
export GIT_AUTHOR_NAME=test
export GIT_AUTHOR_EMAIL=test@example.com
export GIT_AUTHOR_DATE='Thu Jan 1 00:00:00 1970 +0000'
export GIT_COMMITTER_NAME=test
export GIT_COMMITTER_EMAIL=test@example.com
export GIT_COMMITTER_DATE='Thu Jan 1 00:00:00 1970 +0000'

export PATH=$TESTDIR/git/commands:$TESTDIR/venv/git-cinnabar:$PATH

. $TESTDIR/hgext/reviewboard/tests/helpers.sh

gitmozreviewenv() {
  commonenv

  defaultkey=`mozreview create-api-key default@example.com`
  export DEFAULTAPIKEY=${defaultkey}

  cat > $HOME/.gitconfig << EOF
[bz]
username = default@example.com
apikey = ${defaultkey}
trustedapikeyservices = ${MERCURIAL_URL}

[mozreview]
nickname = mynick
EOF

  cat > $HOME/fakegitids << EOF
0
EOF
  export FAKEIDPATH=$HOME/fakegitids

  # seed review repo with public changeset
  cd client
  touch foo
  hg -q commit -A -m initial
  hg phase --public -r .
  hg -q push --noreview

  mozreview exec hgrb /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/autoreview createrepomanifest ${MERCURIAL_URL} ssh://${HGSSH_HOST}:${HGSSH_PORT}/ > /dev/null
}
