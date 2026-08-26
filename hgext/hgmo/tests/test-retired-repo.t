  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh

Create a server for a retired repository

  $ hg init retired
  $ cd retired
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > 
  > [web]
  > push_ssl = False
  > allow_push = *
  > 
  > [readonly]
  > retiredurl = https://github.com/mozilla/nspr
  > EOF
  $ touch foo
  $ hg -q commit -A -m initial
  $ NODE=$(hg log -r . -T "{node}")
  $ hg serve -d -p $HGPORT --pid-file hg.pid --hgmo -E error.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

The banner is displayed on every page of a retired repository

  $ http http://localhost:$HGPORT/ --body-file body > /dev/null
  $ grep -A 2 'retired_banner' body
  <div class="retired_banner">
  This repository is retired and read only.
  The code now lives at <a href="https://github.com/mozilla/nspr">https://github.com/mozilla/nspr</a>.

  $ http http://localhost:$HGPORT/shortlog --body-file body > /dev/null
  $ grep -c 'retired_banner' body
  1

  $ http http://localhost:$HGPORT/rev/$NODE --body-file body > /dev/null
  $ grep -c 'retired_banner' body
  1

  $ http http://localhost:$HGPORT/file/tip --body-file body > /dev/null
  $ grep -c 'retired_banner' body
  1

Create a server for a repository that is not retired

  $ hg init active
  $ cd active
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > 
  > [web]
  > push_ssl = False
  > allow_push = *
  > EOF
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg serve -d -p $HGPORT1 --pid-file hg.pid --hgmo -E error.log
  $ cat hg.pid >> $DAEMON_PIDS
  $ cd ..

No banner is displayed for a repository that is not retired

  $ http http://localhost:$HGPORT1/ --body-file body > /dev/null
  $ grep 'retired_banner' body
  [1]

Confirm no errors in logs

  $ cat retired/error.log
  $ cat active/error.log
