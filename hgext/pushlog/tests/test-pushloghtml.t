  $ . $TESTDIR/hgext/pushlog/tests/helpers.sh
  $ hg init server
  $ cd server
  $ serverconfig .hg/hgrc
  $ export USER=hguser
  $ hg serve -d -p $HGPORT --pid-file hg.pid -E error.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Populate the repo with some data

  $ hg clone http://localhost:$HGPORT client > /dev/null
  $ cd client
  $ touch foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg push
  pushing to http://$LOCALHOST:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: recorded push in pushlog
  remote: added 1 changesets with 1 changes to 1 files

  $ hg branch branch_foo > /dev/null
  $ echo foo1 > foo
  $ hg commit -m 'first commit on branch_foo'
  $ hg push --new-branch > /dev/null
  $ echo foo2 > foo
  $ hg commit -m 'second commit on branch_foo'
  $ hg tag -m 'tagging foo2' foo2
  $ hg push > /dev/null

  $ hg up -r 0 > /dev/null
  $ hg branch branch_bar > /dev/null
  $ echo bar1 > foo
  $ hg commit -m 'first commit on branch_bar'
  $ echo bar2 > foo
  $ hg commit -m 'second commit on branch_bar'
  $ hg tag -m 'tagging bar2' bar2
  $ hg push --new-branch > /dev/null

Pushlog HTML sanity test

  $ http http://localhost:$HGPORT/pushloghtml --header content-type --no-body
  200
  content-type: text/html; charset=ascii

  $ http http://localhost:$HGPORT/pushloghtml/blah --header content-type --no-body
  200
  content-type: text/html; charset=ascii

Main HTML page lists all pushes

  $ http http://localhost:$HGPORT/pushloghtml --body-file body --no-headers
  200
  $ grep pushlogentry body
  <tr class="pushlogentry parity0  id4"><td><cite>hguser<br/><span class="date">*</span></cite></td><td><a href="/rev/fccd2b8674ef410d3912deb8dbfe53c7fde6bbab">fccd2b8674ef410d3912deb8dbfe53c7fde6bbab</a></td><td><strong>test &mdash; tagging bar2</strong> <span class="logtags"><span class="branchtag" title="branch_bar">branch_bar</span> <span class="tagtag" title="tip">tip</span> </span></td></tr> (glob)
  <tr class="pushlogentry parity0  id4"><td></td><td><a href="/rev/b32e82060ac2416243e6cb8325f77b9743155d39">b32e82060ac2416243e6cb8325f77b9743155d39</a></td><td><strong>test &mdash; second commit on branch_bar</strong> <span class="logtags"><span class="inbranchtag" title="branch_bar">branch_bar</span> <span class="tagtag" title="bar2">bar2</span> </span></td></tr>
  <tr class="pushlogentry parity0  id4"><td></td><td><a href="/rev/925e1c8915ab85a42fad32c244a3d16511362ec4">925e1c8915ab85a42fad32c244a3d16511362ec4</a></td><td><strong>test &mdash; first commit on branch_bar</strong> <span class="logtags"><span class="inbranchtag" title="branch_bar">branch_bar</span> </span></td></tr>
  <tr class="pushlogentry parity1  id3"><td><cite>hguser<br/><span class="date">*</span></cite></td><td><a href="/rev/0cebc5195347dd8baccbf85b25ab8170068d5c83">0cebc5195347dd8baccbf85b25ab8170068d5c83</a></td><td><strong>test &mdash; tagging foo2</strong> <span class="logtags"><span class="branchtag" title="branch_foo">branch_foo</span> </span></td></tr> (glob)
  <tr class="pushlogentry parity1  id3"><td></td><td><a href="/rev/17880384fe19f0157250bab9af41b3f7a7b74db1">17880384fe19f0157250bab9af41b3f7a7b74db1</a></td><td><strong>test &mdash; second commit on branch_foo</strong> <span class="logtags"><span class="inbranchtag" title="branch_foo">branch_foo</span> <span class="tagtag" title="foo2">foo2</span> </span></td></tr>
  <tr class="pushlogentry parity0  id2"><td><cite>hguser<br/><span class="date">*</span></cite></td><td><a href="/rev/a8ffcd74ae3e26c8de570853b7a1adb404aed1f9">a8ffcd74ae3e26c8de570853b7a1adb404aed1f9</a></td><td><strong>test &mdash; first commit on branch_foo</strong> <span class="logtags"><span class="inbranchtag" title="branch_foo">branch_foo</span> </span></td></tr> (glob)
  <tr class="pushlogentry parity1  id1"><td><cite>hguser<br/><span class="date">*</span></cite></td><td><a href="/rev/04caf62ca417ed4e9edfaca2b81c5f68f0e58e7d">04caf62ca417ed4e9edfaca2b81c5f68f0e58e7d</a></td><td><strong>test &mdash; initial commit</strong> <span class="logtags"><span class="branchtag" title="default">default</span> </span></td></tr> (glob)

Using `branch` query string parameter only shows entries for a specific branch

  $ http http://localhost:$HGPORT/pushloghtml?branch=branch_foo --body-file body --no-headers
  200
  $ grep pushlogentry body
  <tr class="pushlogentry parity0  id3"><td><cite>hguser<br/><span class="date">*</span></cite></td><td><a href="/rev/0cebc5195347dd8baccbf85b25ab8170068d5c83">0cebc5195347dd8baccbf85b25ab8170068d5c83</a></td><td><strong>test &mdash; tagging foo2</strong> <span class="logtags"><span class="branchtag" title="branch_foo">branch_foo</span> </span></td></tr> (glob)
  <tr class="pushlogentry parity0  id3"><td></td><td><a href="/rev/17880384fe19f0157250bab9af41b3f7a7b74db1">17880384fe19f0157250bab9af41b3f7a7b74db1</a></td><td><strong>test &mdash; second commit on branch_foo</strong> <span class="logtags"><span class="inbranchtag" title="branch_foo">branch_foo</span> <span class="tagtag" title="foo2">foo2</span> </span></td></tr>
  <tr class="pushlogentry parity1  id2"><td><cite>hguser<br/><span class="date">*</span></cite></td><td><a href="/rev/a8ffcd74ae3e26c8de570853b7a1adb404aed1f9">a8ffcd74ae3e26c8de570853b7a1adb404aed1f9</a></td><td><strong>test &mdash; first commit on branch_foo</strong> <span class="logtags"><span class="inbranchtag" title="branch_foo">branch_foo</span> </span></td></tr> (glob)

A branch that doesn't exist produces an error

  $ http http://localhost:$HGPORT/pushloghtml?branch=branch_asdf --body-file body --no-headers
  404
  $ grep branch_asdf body
  unknown revision 'branch_asdf'

Confirm no errors in log

  $ cat ../server/error.log
