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

Create a new bug and attach a patch

  $ bugzilla create-bug TestProduct TestComponent bug1
  $ echo foo > foo
  $ hg qnew -d '0 0' -m 'Bug 1 - First patch' first-patch
  $ hg bzexport
  Refreshing configuration cache for http://$DOCKER_HOSTNAME:$HGPORT/bzapi/
  first-patch uploaded as http://$DOCKER_HOSTNAME:$HGPORT/attachment.cgi?id=1&action=edit

Use qimport to get it into the mq patch queue

  $ hg qpop -a
  popping bug-1-first-patch
  patch queue now empty
  $ hg qrm bug-1-first-patch

  $ hg qimport bz://1
  Fetching... done
  Parsing... done
  adding 1 to series file
  renamed 1 -> bug-1-first-patch

  $ hg qpush
  applying bug-1-first-patch
  now at: bug-1-first-patch
  $ hg qpop -a
  popping bug-1-first-patch
  patch queue now empty

Stop messing around with mq and do it again normally

  $ hg import bz://1
  applying bz://1
  Fetching... done
  Parsing... done

Do a second patch

  $ echo again >> foo
  $ hg commit -m 'Bug 1 - Second patch'
  $ hg bzexport
  . uploaded as http://$DOCKER_HOSTNAME:$HGPORT/attachment.cgi?id=2&action=edit
  $ hg update -r 'keyword("initial")'
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo all | hg import bz://1
  applying bz://1
  Fetching... done
  Parsing... done
  
  1: First patch
  2: Second patch
  
  Which patches do you want to import, and in which order? [Default is all]
  (eg '1-3,5', or 's' to toggle the sort order between id & patch description) 1-2


  $ hg log -T '{rev} {desc}\n'
  2 Bug 1 - Second patch
  1 Bug 1 - First patch
  0 initial

  $ $TESTDIR/d0cker stop-bmo qimportbz-test-import
  stopped 1 containers
