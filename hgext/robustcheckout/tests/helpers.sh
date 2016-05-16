cat >> $HGRCPATH << EOF
[share]
pool = $TESTTMP/share

[extensions]
robustcheckout = $TESTDIR/hgext/robustcheckout
EOF

mkdir server
hg init server/repo0
hg init server/repo1

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
cd ..

hg -q clone -r 0 --pull -U repo0 repo0-upstream

cat >> hgweb.conf << EOF
[paths]
/ = $TESTTMP/server/*
EOF

hg serve -d -p $HGPORT --pid-file hg.pid --web-conf hgweb.conf
cat hg.pid >> $DAEMON_PIDS

cd $TESTTMP