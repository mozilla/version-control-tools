  $ . $TESTDIR/hgext/pushlog-legacy/tests/helpers.sh
  $ hg init server
  $ cd server
  $ serverconfig .hg/hgrc
  $ export USER=hguser
  $ hg serve -d -p $HGPORT --pid-file hg.pid
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

Populate the repo with some data

  $ hg clone http://localhost:$HGPORT client > /dev/null
  $ cd client
  $ touch foo
  $ hg commit -A -m 'initial commit'
  adding foo
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.

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

Main HTML page lists all pushes

  $ http http://localhost:$HGPORT/pushloghtml --body-file body --no-headers
  200
  $ python $TESTDIR/testing/xmldump.py body "//*[contains(@class, 'pushlogentry')]"
  <tr xmlns="http://www.w3.org/1999/xhtml" class="pushlogentry parity0  id4">
    <td>
      <cite>hguser<br /><span class="date">*</span></cite> (glob)
    </td>
    <td class="age">
      <a href="/rev/fccd2b8674ef">fccd2b8674ef</a>
    </td>
    <td><strong>test &mdash; tagging bar2</strong> <span class="logtags"><span class="inbranchtag" title="branch_bar">branch_bar</span> <span class="tagtag" title="tip">tip</span> </span></td>
  </tr>
  <tr xmlns="http://www.w3.org/1999/xhtml" class="pushlogentry parity0  id4">
    <td></td>
    <td class="age">
      <a href="/rev/b32e82060ac2">b32e82060ac2</a>
    </td>
    <td><strong>test &mdash; second commit on branch_bar</strong> <span class="logtags"><span class="inbranchtag" title="branch_bar">branch_bar</span> <span class="tagtag" title="bar2">bar2</span> </span></td>
  </tr>
  <tr xmlns="http://www.w3.org/1999/xhtml" class="pushlogentry parity0  id4">
    <td></td>
    <td class="age">
      <a href="/rev/925e1c8915ab">925e1c8915ab</a>
    </td>
    <td><strong>test &mdash; first commit on branch_bar</strong> <span class="logtags"><span class="inbranchtag" title="branch_bar">branch_bar</span> </span></td>
  </tr>
  <tr xmlns="http://www.w3.org/1999/xhtml" class="pushlogentry parity1  id3">
    <td>
      <cite>hguser<br /><span class="date">*</span></cite> (glob)
    </td>
    <td class="age">
      <a href="/rev/0cebc5195347">0cebc5195347</a>
    </td>
    <td><strong>test &mdash; tagging foo2</strong> <span class="logtags"><span class="inbranchtag" title="branch_foo">branch_foo</span> </span></td>
  </tr>
  <tr xmlns="http://www.w3.org/1999/xhtml" class="pushlogentry parity1  id3">
    <td></td>
    <td class="age">
      <a href="/rev/17880384fe19">17880384fe19</a>
    </td>
    <td><strong>test &mdash; second commit on branch_foo</strong> <span class="logtags"><span class="inbranchtag" title="branch_foo">branch_foo</span> <span class="tagtag" title="foo2">foo2</span> </span></td>
  </tr>
  <tr xmlns="http://www.w3.org/1999/xhtml" class="pushlogentry parity0  id2">
    <td>
      <cite>hguser<br /><span class="date">*</span></cite> (glob)
    </td>
    <td class="age">
      <a href="/rev/a8ffcd74ae3e">a8ffcd74ae3e</a>
    </td>
    <td><strong>test &mdash; first commit on branch_foo</strong> <span class="logtags"><span class="inbranchtag" title="branch_foo">branch_foo</span> </span></td>
  </tr>
  <tr xmlns="http://www.w3.org/1999/xhtml" class="pushlogentry parity1  id1">
    <td>
      <cite>hguser<br /><span class="date">*</span></cite> (glob)
    </td>
    <td class="age">
      <a href="/rev/04caf62ca417">04caf62ca417</a>
    </td>
    <td><strong>test &mdash; initial commit</strong> <span class="logtags"></span></td>
  </tr>
