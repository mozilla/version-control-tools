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

Query with fromchange and an endID

  $ http "http://localhost:$HGPORT/json-pushes?fromchange=cc07cc0e87f8&endID=15" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare body $TESTDATA/test-repo-fromchange-endid-query.json

Query with a startID and tochange

  $ http "http://localhost:$HGPORT/json-pushes?startID=5&tochange=af5fb85d9324" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare body $TESTDATA/test-repo-startid-tochange-query.json

Query for a single changeset

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare body $TESTDATA/test-repo-changeset-query.json

Query for two changesets at once

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c&changeset=a79451771352" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare body $TESTDATA/test-repo-multi-changeset-query.json

Query a changeset that doesn't exist

  $ http "http://localhost:$HGPORT/json-pushes?changeset=foobar" --header content-type --body-file body
  404
  content-type: application/json

  $ cat body
  "unknown revision 'foobar'" (no-eol)

Format version 1 works

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c&version=1" --header content-type --body-file body
  200
  content-type: application/json

  $ cat body
  {
   "16": {
    "changesets": [
     "91826025c77c6a8e5711735adaa9766dd4eac7fc", 
     "25f2a69ac7ac2919ef35c0b937b862fbb9e7e1f7"
    ], 
    "date": 1227196396, 
    "user": "luser"
   }
  } (no-eol)

Format version 3 fails

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c&version=3" --header content-type --body-file body
  500
  content-type: application/json

  $ cat body
  "version parameter must be 1 or 2" (no-eol)

Format version 2 has pushes in a child object and a last push id

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c&version=2" --header content-type --body-file body
  200
  content-type: application/json

  $ cat body
  {
   "lastpushid": 21, 
   "pushes": {
    "16": {
     "changesets": [
      "91826025c77c6a8e5711735adaa9766dd4eac7fc", 
      "25f2a69ac7ac2919ef35c0b937b862fbb9e7e1f7"
     ], 
     "date": 1227196396, 
     "user": "luser"
    }
   }
  } (no-eol)

Querying against a startID that is too high results in an error

  $ http "http://localhost:$HGPORT/json-pushes?startID=9999&version=2" --header content-type --body-file body
  200
  content-type: application/json

  $ cat body
  {
   "errorcode": "PUSH_ID_GREATER_THAN_AVAILABLE", 
   "errormessage": "Push ID not found: 9999", 
   "lastpushid": 21
  } (no-eol)

Same failure on version 1 returns an empty set (for backwards compatibility)

  $ http "http://localhost:$HGPORT/json-pushes?startID=9999" --header content-type --body-file body
  200
  content-type: application/json

  $ cat body
  {} (no-eol)
