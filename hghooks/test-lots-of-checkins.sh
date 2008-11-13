#!/bin/sh
# This script tests the pushlog hook. I've only run it on OS X, so be warned.
# This is mostly just to generate a repo for testing the pushlog web output.

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

# push lots of changes
echo "checkin 1" > $CLONE/testfile
hg add -R $CLONE $CLONE/testfile
hg ci -R $CLONE -m "checkin 1"
hg push -R $CLONE $REPO;

for ((i=2; $i<=200; i++)); do
  echo "checkin $i" >> $CLONE/testfile;
  hg ci -R $CLONE -m "checkin $i";
  hg push -R $CLONE $REPO;
done

# Test total push count
EXPECTED_PUSHCOUNT=200
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
