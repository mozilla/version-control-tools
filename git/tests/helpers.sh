# make git commits deterministic and environment agnostic
export GIT_AUTHOR_NAME=test
export GIT_AUTHOR_EMAIL=test@example.com
export GIT_AUTHOR_DATE='Thu Jan 1 00:00:00 1970 +0000'
export GIT_COMMITTER_NAME=test
export GIT_COMMITTER_EMAIL=test@example.com
export GIT_COMMITTER_DATE='Thu Jan 1 00:00:00 1970 +0000'

export PATH=$TESTDIR/git/commands:$TESTDIR/venv/git-cinnabar:$PATH

. $TESTDIR/hgext/reviewboard/tests/helpers.sh
