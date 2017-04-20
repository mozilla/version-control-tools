# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

. $TESTDIR/hgserver/tests/helpers.sh

# make git commits deterministic and environment agnostic
export GIT_AUTHOR_NAME=test
export GIT_AUTHOR_EMAIL=test@example.com
export GIT_AUTHOR_DATE='Thu Jan 1 00:00:00 1970 +0000'
export GIT_COMMITTER_NAME=test
export GIT_COMMITTER_EMAIL=test@example.com
export GIT_COMMITTER_DATE='Thu Jan 1 00:00:00 1970 +0000'

export BETAMAX_LIBRARY_DIR=$TESTDIR/vcssync/tests/cassettes

standardgitrepo() {
    here=`pwd`
    git init $1
    cd $1
    echo 0 > foo
    git add foo
    git commit -m initial
    cat > file0 << EOF
file0 0
file0 1
file0 2
file0 3
file0 4
file0 5
file0 6
file0 7
file0 8
file0 9
file0 10
EOF
    cat > file1 << EOF
file1 0
file1 1
file1 2
file1 3
file1 4
file1 5
file1 6
file1 7
file1 8
file1 9
EOF

    git add file0 file1
    git commit -m 'add file0 and file1'
    cp file0 file0-copy0
    git add file0-copy0
    git commit -m 'copy file0 to file0-copy0'
    cp file0 file0-copy1
    cp file0 file0-copy2
    git add file0-copy1 file0-copy2
    git commit -m 'copy file0 to file0-copy1 and file0-copy2'
    git mv file0 file0-moved
    git commit -m 'move file0 to file0-moved'

    # Make copy then move source so default copy detection kicks in
    cp file0-moved file0-copied-with-move
    git mv file0-moved file0-moved-with-copy
    git add file0-copied-with-move
    git commit -m 'copy file0-moved and rename source'

    # Create copies of file1 with modifications
    cat > file1-20 << EOF
file1 2
file1 7
EOF

    cat > file1-50 << EOF
file1 0
file1 1
file1 2
file1 3
file1 4
EOF

   cat > file1-80 << EOF
file1 0
file1 1
file1 2
file1 3
file1 5
file1 6
file1 7
file1 9
EOF

    git add file1-20 file1-50 file1-80
    git commit -m 'create file1-20, file1-50 and file1-80 as copies with mods'

    git branch head2
    echo 1 > foo
    git add foo
    git commit -m 'dummy commit 1 on master'
    echo 2 > foo
    git add foo
    git commit -m 'dummy commit 2 on master'
    git checkout head2
    echo 3 > bar
    git add bar
    git commit -m 'dummy commit 1 on head2'
    echo 4 > bar
    git add bar
    git commit -m 'dummy commit 2 on head2'
    git checkout master
    git merge head2
    echo 5 > foo
    git add foo
    git commit -m 'dummy commit 1 after merge'

    cd $here
}

standardoverlayenv() {
    cat >> $HGRCPATH <<EOF
[extensions]
overlay=$TESTDIR/hgext/overlay

[overlay]
sourceurl = http://example.com/dummy-overlay-source
EOF

    mkdir server
    cd server
    hg init overlay-source
    cd overlay-source
    echo source-file0 > source-file0
    echo source-file1 > source-file1
    hg commit -A -m 'initial - add source-file0 and source-file1'
    mkdir dir0
    echo 1 > dir0/file0
    hg commit -A -m 'add dir0/file0'
    cd ..

    hg init overlay-dest
    cd overlay-dest
    touch dest-file0 dest-file1
    hg commit -A -m 'initial in dest'
    cd ..

    cat > hgweb.conf <<EOF
[paths]
/ = $TESTTMP/server/*
[web]
refreshinterval = -1
allow_push = *
push_ssl = False
EOF

    hg serve -d -p $HGPORT --pid-file hg.pid --web-conf hgweb.conf
    cat hg.pid >> $DAEMON_PIDS
    cd ..
}
