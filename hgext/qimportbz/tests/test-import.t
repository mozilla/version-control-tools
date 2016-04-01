#require bmodocker
  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > mq =
  > 
  > qimportbz = $TESTDIR/hgext/qimportbz
  > 
  > [qimportbz]
  > bugzilla = http://${DOCKER_HOSTNAME}:$HGPORT
  > EOF

  $ $TESTDIR/d0cker start-bmo qimportbz-test-import $HGPORT
  waiting for Bugzilla to start
  Bugzilla accessible on http://$DOCKER_HOSTNAME:$HGPORT/

  $ . $TESTDIR/hgext/bzexport/tests/helpers.sh
  $ configurebzexport $HGPORT $HGRCPATH

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg -q commit -A -m initial

  $ bugzilla create-bug TestProduct TestComponent bug1
  $ echo foo > foo
  $ hg qnew -d '0 0' -m 'Bug 1 - First patch' first-patch
  $ hg bzexport
  Refreshing configuration cache for http://$DOCKER_HOSTNAME:$HGPORT/bzapi/
  first-patch uploaded as http://$DOCKER_HOSTNAME:$HGPORT/attachment.cgi?id=1&action=edit

  $ hg qpop -a
  popping first-patch
  patch queue now empty
  $ hg qrm first-patch

  $ hg qimport bz://1
  Fetching... done
  Parsing... done
  adding 1 to series file
  renamed 1 -> first-patch

  $ $TESTDIR/d0cker stop-bmo qimportbz-test-import
  stopped 1 containers
