#!/bin/sh
# This script tests the pushlog converter script. I've only run it on OS X, so be warned.

SCRIPTDIR=`dirname $0`

rm -rf /tmp/hghooks
# pull an older revision so we can test using the older hooks and converting
hg clone -r 6209a348c992 http://hg.mozilla.org/users/bsmedberg_mozilla.com/index.cgi/hghooks/ /tmp/hghooks

# need the record script in PATH
export PATH=$PATH:/tmp/hghooks

REPO=/tmp/hg-test
CLONE=${REPO}-clone
# cleanup any existing stuff
rm -rf $REPO $CLONE

# create a new hg repo
mkdir $REPO
hg init $REPO

# setup the old flatfile pushlog hook
cat > $REPO/.hg/hgrc <<EOF
[hooks]
pretxnchangegroup.z_linearhistory = hg_record_changeset_info
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

# then two together
echo "checkin 4" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 4"

echo "checkin 5" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 5"
hg push -R $CLONE $REPO

# now switch to the previous python+sqlite hook, and run the old convert script
export PYTHONPATH=/tmp/hghooks

cat > $REPO/.hg/hgrc <<EOF
[hooks]
pretxnchangegroup.z_linearhistory = python:mozhghooks.pushlog.log
EOF

python /tmp/hghooks/convert-pushlog-db.py $REPO/.hg/pushlog || ( echo "FAIL: failed to convert flat-file -> sqlite" && exit 1 ) || exit 1

# Now push a few more things
# two together, first
echo "checkin 6" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 6"

echo "checkin 7" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 7"
hg push -R $CLONE $REPO

# then one separately
echo "checkin 8" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 8"
hg push -R $CLONE $REPO

# finally two more together
echo "checkin 9" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 6"

echo "checkin 10" >> $CLONE/testfile
hg ci -R $CLONE -m "checkin 10"
hg push -R $CLONE $REPO

# now run the newer convert script
python $SCRIPTDIR/convert-pushlog-db.py $REPO || ( echo "FAIL: failed to convert pushlog.db -> pushlog2.db" && exit 1 ) || exit 1

# Test total push count
PUSHCOUNT=`echo "SELECT COUNT(*) FROM pushlog;" | sqlite3 $REPO/.hg/pushlog2.db`
if [[ "$PUSHCOUNT" != "6" ]]; then
    echo "FAIL: push count $PUSHCOUNT != 6";
    exit 1;
else
    echo "PASS: push count correct";
fi

# Test stored changesets
hg log -R $REPO --template="{node}\n" > /tmp/hg-log-output
echo "SELECT node from changesets LEFT JOIN pushlog ON pushlog.id = changesets.pushid ORDER BY pushid DESC, rev DESC;" | sqlite3 $REPO/.hg/pushlog2.db > /tmp/pushlog-output

if diff /tmp/hg-log-output /tmp/pushlog-output >/dev/null; then
    echo "PASS: recorded and converted all changesets";
else
    echo "FAIL: hg log and pushlog changesets differ!";
    exit 1;
fi

echo "Passed all tests!"
