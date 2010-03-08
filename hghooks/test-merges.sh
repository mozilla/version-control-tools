#!/bin/bash
# This script tests the pushlog hook. I've only run it on OS X, so be warned.

export PYTHONPATH=`dirname $0`

REPO=/tmp/hg-test
CLONE=${REPO}-clone
BRANCH=${REPO}-branch
# cleanup any existing stuff
rm -rf $REPO $CLONE $BRANCH

# create a new hg repo 
mkdir $REPO
hg init $REPO

# setup the pushlog hook
cat > $REPO/.hg/hgrc <<EOF
[hooks]
pretxnchangegroup.z_linearhistory = python:mozhghooks.pushlog.log
EOF

# now clone it, then commit and push some things
hg clone $REPO $CLONE

# push two changes together (clone -> repo)
echo "checkin 1" > $CLONE/testfile
hg add -R $CLONE $CLONE/testfile
hg ci -R $CLONE -m "checkin 1"

echo "checkin 2" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 2"
hg push -R $CLONE $REPO

# then one separately
echo "checkin 3" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 3"
hg push -R $CLONE $REPO


#-----------
# Now clone a branch
hg clone $REPO $BRANCH

# now commit a few changes to the branch
echo "checkin 1" > $BRANCH/testfile2
hg add -R $BRANCH $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 1"

echo "checkin 2" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 2"

echo "checkin 3" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 3"

echo "checkin 4" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 4"

echo "checkin 5" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 5"

# Check in something else in the clone, and push
echo "checkin 4" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 4"
hg push -R $CLONE $REPO

# Now merge from branch
hg pull -R $CLONE $BRANCH
hg update -R $CLONE
hg merge -R $CLONE
hg ci -R $CLONE -m "merge from hg-test-branch"
hg push -R $CLONE $REPO

# check in a few more things just for kicks
echo "checkin 5" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 5"

echo "checkin 6" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 6"
hg push -R $CLONE $REPO

# More branch checkins
echo "checkin 6" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 6"

echo "checkin 7" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 7"

echo "checkin 8" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 8"

echo "checkin 9" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 9"

echo "checkin 10" > $BRANCH/testfile2
hg ci -R $BRANCH -m "branch checkin 10"

# Now merge from branch
hg pull -R $CLONE $BRANCH
hg update -R $CLONE
hg merge -R $CLONE
hg ci -R $CLONE -m "merge from hg-test-branch"
hg push -R $CLONE $REPO

# Test total push count
EXPECTED_PUSHCOUNT=6
PUSHCOUNT=`echo "SELECT COUNT(*) FROM pushlog;" | sqlite3 $REPO/.hg/pushlog2.db`
if [[ "$PUSHCOUNT" != "$EXPECTED_PUSHCOUNT" ]]; then
    echo "FAIL: push count $PUSHCOUNT != $EXPECTED_PUSHCOUNT";
    exit 1;
else
    echo "PASS: push count correct";
fi

# Test stored changesets
hg log -R $REPO --template="{node}\n" > /tmp/hg-log-output
echo "SELECT node from changesets LEFT JOIN pushlog ON pushlog.id = changesets.pushid ORDER BY pushid DESC, rev DESC;" | sqlite3 $REPO/.hg/pushlog2.db > /tmp/pushlog-output

if diff /tmp/hg-log-output /tmp/pushlog-output >/dev/null; then
    echo "PASS: recorded all changesets";
else
    echo "FAIL: hg log and pushlog changesets differ!";
    exit 1;
fi

echo "Passed all tests!"
