#!/bin/sh
# This script tests the pushlog hook. I've only run it on OS X, so be warned.

export PYTHONPATH=`dirname $0`

REPO=/tmp/hg-test
CLONE=${REPO}-clone
# cleanup any existing stuff
rm -rf $REPO $CLONE

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

# push two changes together first
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

# then three together
echo "checkin 4" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 4"

echo "checkin 5" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 5"

echo "checkin 6" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 6"
hg push -R $CLONE $REPO

# Test total push count
PUSHCOUNT=`echo "SELECT COUNT(*) FROM pushlog;" | sqlite3 $REPO/.hg/pushlog2.db`
if [[ "$PUSHCOUNT" != "3" ]]; then
    echo "FAIL: push count $PUSHCOUNT != 3";
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
