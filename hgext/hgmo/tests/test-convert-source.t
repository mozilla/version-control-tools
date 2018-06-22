  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh

  $ cat >> $HGRCPATH << EOF
  > [hgmo]
  > convertsource = /mozilla-central
  > EOF

  $ startserver

  $ hg init orig
  $ cd orig
  $ touch foo
  $ hg -q commit -A -m initial
  $ echo 1 > foo
  $ hg commit -m 1
  $ echo 2 > foo
  $ hg commit -m 2
  $ cd ..

  $ hg -q clone http://localhost:$HGPORT client

  $ cd client
  $ hg -q --config extensions.convert= --config convert.hg.saverev=true convert ../orig .
  $ hg -q push

  $ http http://localhost:$HGPORT/rev/3f1e8da7de66 --body-file body > /dev/null
  $ grep converted body
  <tr><td>converted from</td><td><a href="/mozilla-central/rev/c0f2344539c41be3e493656d83a59306f9395e2f">c0f2344539c41be3e493656d83a59306f9395e2f</a></td></tr>

Confirm no errors in log

  $ cat ../server/error.log
