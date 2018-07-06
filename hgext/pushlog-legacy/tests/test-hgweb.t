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
  <tr class="pushlogentry parity0  id21"><td><cite>luser<br/><span class="date">Thu Nov 20 15:53:42 2008 +0000</span></cite></td><td><a href="/rev/427bfb5defee">427bfb5defee</a></td><td><strong>Ted Mielczarek &mdash; checkin 41</strong> <span class="logtags"><span class="tagtag" title="tip">tip</span> </span></td></tr>

Get all JSON data

  $ http "http://localhost:$HGPORT/json-pushes?startID=0" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare $TESTDATA/test-repo-data.json body

Get all JSON data with details

  $ http "http://localhost:$HGPORT/json-pushes?startID=0&full=1" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare $TESTDATA/test-repo-data-full.json body

Query with fromchange and an endID

  $ http "http://localhost:$HGPORT/json-pushes?fromchange=cc07cc0e87f8&endID=15" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare $TESTDATA/test-repo-fromchange-endid-query.json body

Query with a startID and tochange

  $ http "http://localhost:$HGPORT/json-pushes?startID=5&tochange=af5fb85d9324" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare $TESTDATA/test-repo-startid-tochange-query.json body

Query for a single changeset

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare $TESTDATA/test-repo-changeset-query.json body

Query for two changesets at once

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c&changeset=a79451771352" --header content-type --body-file body
  200
  content-type: application/json

  $ jsoncompare $TESTDATA/test-repo-multi-changeset-query.json body

Query a changeset that doesn't exist

  $ http "http://localhost:$HGPORT/json-pushes?changeset=foobar" --header content-type --body-file body
  404
  content-type: application/json

  $ cat body
  "unknown revision 'foobar'" (no-eol)

Test paging

  $ http "http://localhost:$HGPORT/json-pushes/1?version=2" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "lastpushid": 21,
      "pushes": {
          "12": {
              "changesets": [
                  "cc07cc0e87f8d80baf8242a2f27b610bc16e03a8",
                  "7886a3f7fcba196c29bd9de0cc4d858cdc4910b9"
              ],
              "date": 1227196375,
              "user": "luser"
          },
          "13": {
              "changesets": [
                  "7d6c2c9744fe87b74aa6adce043c597dbdbb53b5",
                  "4ccee53e18ac923ff9ac995805748167128327a9"
              ],
              "date": 1227196380,
              "user": "luser"
          },
          "14": {
              "changesets": [
                  "db80b071182be2384ba703f77a135a637e9a184a",
                  "853ae4aff7ec183c47f8b9b08faff9f8f4083855"
              ],
              "date": 1227196385,
              "user": "luser"
          },
          "15": {
              "changesets": [
                  "41720e1fcc1c24ffd16cd988b5d8fbbe1fe23c90",
                  "af5fb85d93246318a4050c4def448cbcfd068e57"
              ],
              "date": 1227196390,
              "user": "luser"
          },
          "16": {
              "changesets": [
                  "91826025c77c6a8e5711735adaa9766dd4eac7fc",
                  "25f2a69ac7ac2919ef35c0b937b862fbb9e7e1f7"
              ],
              "date": 1227196396,
              "user": "luser"
          },
          "17": {
              "changesets": [
                  "759b21a48c09dfc221107268e84c71c32d48c84b",
                  "6437207053fb9701290b738d720044803436ba3e"
              ],
              "date": 1227196401,
              "user": "luser"
          },
          "18": {
              "changesets": [
                  "6af3e4a04e2dd1491fc63c5b0cd811429452abc2",
                  "0ea9c66e27948fde116fbaa141bb53e9f7c23359"
              ],
              "date": 1227196406,
              "user": "luser"
          },
          "19": {
              "changesets": [
                  "cf831767c52b75f1c57aa41d586877f9d18d61fa",
                  "a79451771352e444711b99134174c5daa05db9cd"
              ],
              "date": 1227196412,
              "user": "luser"
          },
          "20": {
              "changesets": [
                  "ed2e46ccf6357ec678bf02e77dd7ef0efa308c4b",
                  "5995073215aee645700749a66989b1936b5f4ca6"
              ],
              "date": 1227196417,
              "user": "luser"
          },
          "21": {
              "changesets": [
                  "bd6a28608e15b54c145f0af9015ef5dbca3462d6",
                  "427bfb5defee1bbe75f3fcd8a86be3ad33657e95"
              ],
              "date": 1227196422,
              "user": "luser"
          }
      }
  }

  $ http "http://localhost:$HGPORT/json-pushes/2?version=2" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "lastpushid": 21,
      "pushes": {
          "10": {
              "changesets": [
                  "ccf92322df622434a5b74cdecb52f5c01e7b4386",
                  "a19f3496dc6d46e9b22bda92676bb20bacd3124a"
              ],
              "date": 1227196364,
              "user": "luser"
          },
          "11": {
              "changesets": [
                  "d19fa6e892483a197ba0138d996ef3621828f9ea",
                  "e9ea8b142bf4e2aa230cbd46d68ec73f45c1e080"
              ],
              "date": 1227196369,
              "user": "luser"
          },
          "2": {
              "changesets": [
                  "72fd4cbf4f882f9a45f5771791e38c4060d221ee",
                  "83ce6c6fee7b76b83019e681f922dc19c0e60a6a"
              ],
              "date": 1227196322,
              "user": "luser"
          },
          "3": {
              "changesets": [
                  "867c3a4513ed8631d77a89e49edc47dcc90fcbe6",
                  "5013972f6450b79fc1a804eee3fb9b7aa9f1d96b"
              ],
              "date": 1227196327,
              "user": "luser"
          },
          "4": {
              "changesets": [
                  "083f3e712107f22576670e210ea794bed8a83eb2",
                  "943ccca41b66f26d1a3403ccd628a5dd7ad57347"
              ],
              "date": 1227196332,
              "user": "luser"
          },
          "5": {
              "changesets": [
                  "df4b1b9d7d1c5ae66ae8b125c0c1fe4311bdbb30",
                  "08457a6ebdd3c616246e120e0c4b912ff837e1d9"
              ],
              "date": 1227196338,
              "user": "luser"
          },
          "6": {
              "changesets": [
                  "784ff898cfb79d00df5fcbad75af3d64bed6c696",
                  "5a12fe530992a84722c00ec6afa632c7fcf31093"
              ],
              "date": 1227196343,
              "user": "luser"
          },
          "7": {
              "changesets": [
                  "2d6b2af9c95bc8884d9555aba5e4f4a843f3550b",
                  "1ab7868c33f5a8db756bfaaa4fef148af7a983e3"
              ],
              "date": 1227196348,
              "user": "luser"
          },
          "8": {
              "changesets": [
                  "01ffeda797534f3045ad1cd941fddc3b775d8335",
                  "82883a615a97e9d5bd2083787fba2589dcfb4d7f"
              ],
              "date": 1227196353,
              "user": "luser"
          },
          "9": {
              "changesets": [
                  "14f8472e2d04432be45987fe3ac2d3440b11264d",
                  "d091969e89a9581fd89f7ed0afce10aaaa0c24bf"
              ],
              "date": 1227196359,
              "user": "luser"
          }
      }
  }

Format version 1 works

  $ http "http://localhost:$HGPORT/json-pushes?changeset=91826025c77c&version=1" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "16": {
          "changesets": [
              "91826025c77c6a8e5711735adaa9766dd4eac7fc",
              "25f2a69ac7ac2919ef35c0b937b862fbb9e7e1f7"
          ],
          "date": 1227196396,
          "user": "luser"
      }
  }

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

  $ python -m json.tool < body
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
  }

Confirm no errors in log

  $ cat ./server/error.log
