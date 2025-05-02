  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh
  $ startserver

  $ hg -q clone http://localhost:$HGPORT client
  $ cd client
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > commitextra = $TESTDIR/hgext/hgmo/tests/commitextra.py
  > EOF

  $ echo initial > foo
  $ hg add foo
  $ hg -q commit -m initial
  $ INITIAL=$(hg log -r . -T "{node}")
  $ echo git_blah > git_blah
  $ hg add git_blah
  $ hg -q commit -m 'test adding git commit' --extra "git_commit=bee43b04ef40b15ae222c9d935a76388a4d5b0a3"
  $ GIT_COMMIT=$(hg log -r . -T "{node}")

  $ hg -q push

No Git URL if there is no `git_commit`.

  $ http http://localhost:$HGPORT/rev/$INITIAL --body-file body > /dev/null
  $ grep '<td>git commit' body
  [1]

Introduction of commit with `git_commit` extra should show URL.

  $ http http://localhost:$HGPORT/rev/$GIT_COMMIT --body-file body > /dev/null
  $ grep '<td>git commit' body
  <tr><td>git commit</td><td>><a href="https://github.com/mozilla-firefox/firefox/commit/bee43b04ef40b15ae222c9d935a76388a4d5b0a3" target="_blank">bee43b04ef40b15ae222c9d935a76388a4d5b0a3</a></td></tr>

Confirm no errors in log

  $ cat ../server/error.log
