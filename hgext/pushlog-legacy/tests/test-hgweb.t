  $ . $TESTDIR/hgext/pushlog-legacy/tests/helpers.sh
  $ mkdir server
  $ cd server
  $ export TESTDATA=$TESTDIR/hgext/pushlog-legacy/testdata
  $ tar xjf $TESTDATA/test-repo.tar.bz2
  $ serverconfig .hg/hgrc

  $ hg serve -d -p $HGPORT --pid-file hg.pid -A access.log -E error.log
  $ cat hg.pid >> $DAEMON_PIDS

  $ cd ..

Sanity check the html output

  $ http http://localhost:$HGPORT/pushloghtml --header content-type --body-file body
  200
  content-type: text/html; charset=ascii

  $ grep 427bfb5defee body
  <tr class="pushlogentry parity0  id21"><td><cite>luser<br/><span class="date">Thu Nov 20 15:53:42 2008 +0000</span></cite></td><td class="age"><a href="/rev/427bfb5defee">427bfb5defee</a></td><td><strong>Ted Mielczarek &mdash; checkin 41</strong> <span class="logtags"><span class="tagtag" title="tip">tip</span> </span></td></tr>

Get all JSON data

  $ http "http://localhost:$HGPORT/json-pushes?startID=0" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare body $TESTDATA/test-repo-data.json

Get all JSON data with details

  $ http "http://localhost:$HGPORT/json-pushes?startID=0&full=1" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare body $TESTDATA/test-repo-data-full.json
