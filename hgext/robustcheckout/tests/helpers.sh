# We need to unset this otherwise tests running on Taskcluster have
# extra output.
unset TASKCLUSTER_INSTANCE_TYPE

cat >> $HGRCPATH << EOF
[share]
pool = $TESTTMP/share

[extensions]
robustcheckout = $TESTDIR/hgext/robustcheckout

[robustcheckout]
retryjittermin = 0
retryjittermax = 100
EOF

mkdir server
hg init server/repo0
hg init server/repo1
hg init server/bad-server

cd server/repo0

touch foo
hg -q commit -A -m initial0
echo 1 > foo
hg commit -m 1
hg -q up -r 0
hg -q branch branch1
echo branch1 > foo
hg commit -m branch1

cd ../repo1
touch foo
hg -q commit -A -m initial1
echo 1 > foo
hg commit -m 1
cd ../bad-server

cat >> .hg/hgrc << EOF
[extensions]
badserver = $TESTDIR/hgext/robustcheckout/tests/badserver.py
EOF

touch foo
hg -q commit -A -m initial
echo 1 > foo
hg commit -m 'commit 1'

cd ..

hg -q clone -r 0 --pull -U repo0 repo0-upstream

cat >> hgweb.conf << EOF
[paths]
/ = $TESTTMP/server/*
[web]
refreshinterval = -1
EOF

hg serve -d -p $HGPORT --pid-file hg.pid --web-conf hgweb.conf -E error.log
cat hg.pid >> $DAEMON_PIDS

cd $TESTTMP
