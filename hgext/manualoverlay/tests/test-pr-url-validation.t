  $ . $TESTDIR/hgext/manualoverlay/tests/helpers.sh

  $ hg init source
  $ cd source
  $ echo "file1" > file1
  $ hg add file1
  $ hg commit -m "Initial commit"
  $ echo "updated-file1" > file1

Test passing a non-url
  $ hg commit --manualservosync "not-a-well-formed-url"
  abort: --manualservosync was not a proper github pull request url
  (url must be to a servo/servo pull request of the form https://github.com/servo/servo/pull/<pr-number>)
  [255]

Test passing a url to a non servo/servo pull request
  $ hg commit --manualservosync "https://github.com/wrong/repo/pull/17455"
  abort: --manualservosync was not a proper github pull request url
  (url must be to a servo/servo pull request of the form https://github.com/servo/servo/pull/<pr-number>)
  [255]

Test passing a url with an alphanumeric pull request id
  $ hg commit --manualservosync "https://github.com/servo/servo/pull/abc123"
  abort: --manualservosync was not a proper github pull request url
  (url must be to a servo/servo pull request of the form https://github.com/servo/servo/pull/<pr-number>)
  [255]

Committing without --manualservosync should still work
  $ hg commit -m "Normal Commit"
  $ hg log -r .
  changeset:   1:94650105917f
  tag:         tip
  user:        Test User <someone@example.com>
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Normal Commit
  

Overlay extra data shouldn't exist on a normal commit
  $ hg log -r . --template '{extras}'
  branch=default (no-eol)
