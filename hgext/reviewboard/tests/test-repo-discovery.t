#require docker

  $ . $TESTDIR/hgext/reviewboard/tests/helpers.sh
  $ commonenv

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > reviewboard = $TESTDIR/hgext/reviewboard/client.py
  > [reviewboard]
  > fakeids = true
  > [ui]
  > ssh = $TESTDIR/testing/mozreview-ssh
  > [mozilla]
  > ircnick = dummy
  > [bugzilla]
  > username = ${BUGZILLA_USERNAME}
  > password = ${BUGZILLA_PASSWORD}
  > EOF

  $ bugzilla create-bug TestProduct TestComponent bug1

  $ export PUSHPREFIX=ssh://${HGSSH_HOST}:${HGSSH_PORT}

Create some repositories to discover from

  $ mozreview create-repo a
  HTTP URL (read only): http://*:$HGPORT/a (glob)
  SSH URL (read+write): ssh://*:$HGPORT6/a (glob)
  
  Run the following to create a configured clone:
    ./mozreview clone a /path/to/clone
  
  And a clone bound to a particular user:
    ./mozreview clone a /path/to/clone --user <user>
  $ mozreview create-repo b
  HTTP URL (read only): http://*:$HGPORT/b (glob)
  SSH URL (read+write): ssh://*:$HGPORT6/b (glob)
  
  Run the following to create a configured clone:
    ./mozreview clone b /path/to/clone
  
  And a clone bound to a particular user:
    ./mozreview clone b /path/to/clone --user <user>

  $ mkdir repos
  $ cd repos
The sleep here patches over an apparent race condition. It is a hacky
workaround to an unidentified root problem.
  $ sleep 1
  $ hg -q clone ${MERCURIAL_URL}a
  $ cd a
  $ echo foo > foo
  $ hg -q commit -A -m 'Repo a initial'
  $ hg phase --public -r .
  $ hg push --noreview ${PUSHPREFIX}/a
  pushing to ssh://*:$HGPORT6/a (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ hg log -r 0 -T '{node}\n'
  4016108b6e06add4c0ddde40dee8c7b9aa410f58
  $ cd ..

  $ hg -q clone ${MERCURIAL_URL}b
  $ cd b
  $ echo foo > foo
  $ hg -q commit -A -m 'Repo b initial'
  $ hg phase --public -r .

  $ hg push --noreview ${PUSHPREFIX}/b
  pushing to ssh://*:$HGPORT6/b (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog

  $ hg log -r 0 -T '{node}\n'
  36d47cf7c6cbd312de3aeb3b2f770c650b014053
  $ cd ../..

hg createrepomanifest will create and print a manifest of review repos

  $ mozreview exec hgrb hg -R /repo/hg/mozilla/autoreview createrepomanifest
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 http://*:$HGPORT/a (glob)
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 http://*:$HGPORT/b (glob)

Search and replace works

  $ mozreview exec hgrb hg -R /repo/hg/mozilla/autoreview createrepomanifest --search ${MERCURIAL_URL} --replace ${PUSHPREFIX}/
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 ssh://*:$HGPORT6/a (glob)
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 ssh://*:$HGPORT6/b (glob)

createrepomanifest should have created a file

  $ mozreview exec hgrb cat /repo/hg/mozilla/autoreview/.hg/reviewrepos
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 ssh://*:$HGPORT6/a (glob)
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 ssh://*:$HGPORT6/b (glob)

listkeys should give a list of available repositories
(listkeys output isn't stable, hence the excessive globs)

  $ hg debugpushkey ${MERCURIAL_URL}autoreview reviewrepos
  ssh://*:$HGPORT6/*	* (glob)
  ssh://*:$HGPORT6/*	* (glob)

Pushing a repository unrelated to any known repo should result in error message

  $ hg init unrelated
  $ cd unrelated
  $ echo unrelated > foo
  $ hg -q commit -A -m 'Bug 1 - Unrelated repo'
  $ hg push ${PUSHPREFIX}/autoreview
  pushing to ssh://*:$HGPORT6/autoreview (glob)
  searching for appropriate review repository
  abort: no review repository found
  [255]

  $ cd ..

Pushing to autodiscover repo should redirect

  $ hg -q clone ${MERCURIAL_URL}a
  $ cd a
  $ echo discovery > foo
  $ hg commit -m 'Bug 1 - Testing discovery of a'
  $ hg push ${PUSHPREFIX}/autoreview
  pushing to ssh://*:$HGPORT6/autoreview (glob)
  searching for appropriate review repository
  redirecting push to ssh://*:$HGPORT6/a (glob)
  (adding commit id to 1 changesets)
  saved backup bundle to $TESTTMP/a/.hg/strip-backup/e55631d0cc1a*-addcommitid.hg (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  submitting 1 changesets for review
  
  changeset:  1:daa176714e3a
  summary:    Bug 1 - Testing discovery of a
  review:     http://*:$HGPORT1/r/2 (draft) (glob)
  
  review id:  bz://1/dummy
  review url: http://*:$HGPORT1/r/1 (draft) (glob)
  (review requests lack reviewers; visit review url to assign reviewers and publish these review requests)

  $ cd ..

Redirecting ssh:// to http:// should be disallowed (security protection)

  $ mozreview exec hgrb hg -R /repo/hg/mozilla/autoreview createrepomanifest
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 http://*:$HGPORT/a (glob)
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 http://*:$HGPORT/b (glob)

  $ hg -q clone ${MERCURIAL_URL}b
  $ cd b
  $ echo bad_redirect > foo
  $ hg commit -m 'Bug 1 - Testing discovery of b'
  $ hg push ${PUSHPREFIX}/autoreview
  pushing to ssh://*:$HGPORT6/autoreview (glob)
  searching for appropriate review repository
  abort: refusing to redirect due to URL mismatch: http://*:$HGPORT/b (glob)
  [255]

Redirecting to different hostname should be disallowed (security protection)

  $ mozreview exec hgrb hg -R /repo/hg/mozilla/autoreview createrepomanifest --search ${MERCURIAL_URL} --replace ssh://bad.host/
  4016108b6e06add4c0ddde40dee8c7b9aa410f58 ssh://bad.host/a (glob)
  36d47cf7c6cbd312de3aeb3b2f770c650b014053 ssh://bad.host/b (glob)

  $ hg push ${PUSHPREFIX}/autoreview
  pushing to ssh://*:$HGPORT6/autoreview (glob)
  searching for appropriate review repository
  abort: refusing to redirect due to URL mismatch: ssh://bad.host/b (glob)
  [255]

Cleanup

  $ mozreview stop
  stopped 8 containers
