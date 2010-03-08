#!/bin/bash
# This script tests the pushlog hook. I've only run it on OS X, so be warned.
#TODO: port this + the other test scripts to Python using unittest

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
hg ci -R $CLONE -m "checkin 1 bug 12345"

echo "checkin 2" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 2 b=123456"
hg push -R $CLONE $REPO

# then one separately
echo "checkin 3" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 3 - bug345664"
hg push -R $CLONE $REPO

# then three together
echo "checkin 4" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 4 b=111111"

echo "checkin 5" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 5"

echo "checkin 6" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 6"
hg push -R $CLONE $REPO

# Test total push count
EXPECTED_PUSHCOUNT=3
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

# crummy non-portable stat stuff
case `uname` in
  Linux):
        STATARGS='--format=%A'
        ;;
  Darwin):
        STATARGS='-f %Sp'
        ;;
esac

if test -n "$STATARGS"; then
    if [[ `stat $STATARGS $REPO/.hg/pushlog2.db | sed -e "s/^....\(..\).*$/\1/"` != "rw" ]]; then
        echo "FAIL: pushlog db is not group writeable!"
        exit 1;
    else
        echo "PASS: pushlog db is group writeable!"
    fi
fi

# Test that an empty db file doesn't break the hook - bug 466149
rm $REPO/.hg/pushlog2.db
touch $REPO/.hg/pushlog2.db

echo "another checkin" >> $CLONE/testfile
hg ci -R $CLONE -m "another checkin"
if hg push -R $CLONE $REPO; then
    echo "PASS: push to empty db succeeded"
else
    echo "FAIL: failed to push to repo with empty db"
    exit 1;
fi

echo "Passed all tests!"
