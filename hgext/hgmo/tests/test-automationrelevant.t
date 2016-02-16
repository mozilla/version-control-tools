  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to http://localhost:$HGPORT/
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ echo p1_1 > foo
  $ hg commit -m 'push 1 commit 1'
  $ echo p1_2 > foo
  $ hg commit -m 'push 1 commit 2'
  $ hg -q push

  $ echo p2_1 > foo
  $ hg commit -m 'push 2 commit 1'
  $ echo p2_2 > foo
  $ hg commit -m 'push 2 commit 2'
  $ echo p2_3 > foo
  $ hg commit -m 'push 2 commit 3'
  $ hg -q push

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > pushlog = $TESTDIR/hgext/pushlog
  > EOF

  $ cd ../server

Querying the tip of a push should return all changesets in the push

  $ hg log -r 'automationrelevant(2)' -T '{rev} {desc}\n'
  1 push 1 commit 1
  2 push 1 commit 2

  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Middle of a push should return ancestor changesets in the push

  $ hg log -r 'automationrelevant(4)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2

Bottom of a push should return just that changeset

  $ hg log -r 'automationrelevant(1)' -T '{rev} {desc}\n'
  1 push 1 commit 1

  $ hg log -r 'automationrelevant(3)' -T '{rev} {desc}\n'
  3 push 2 commit 1

Now move some phases to draft to verify draft changesets spanning pushes are included

Tip to draft should still return entire push

  $ hg phase -f --draft -r 5
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Tip ancestor to draft should still return entire push

  $ hg phase -f --draft -r 4
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Push base to draft should still return entire push

  $ hg phase -f --draft -r 3
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

  $ hg log -r 'automationrelevant(4)' -T '{rev} {desc}\n'
  3 push 2 commit 1
  4 push 2 commit 2

Previous push head to draft should add it to relevant list

  $ hg phase -f --draft -r 2
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  2 push 1 commit 2
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3

Previous push base to draft should add it to relevant list

  $ hg phase -f --draft -r 1
  $ hg log -r 'automationrelevant(5)' -T '{rev} {desc}\n'
  1 push 1 commit 1
  2 push 1 commit 2
  3 push 2 commit 1
  4 push 2 commit 2
  5 push 2 commit 3
