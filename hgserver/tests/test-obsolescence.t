#require docker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

TODO there appears to be a race condition on locking bug in Mercurial
that triggers when replication of obsolescence markers is performed.
http://bz.selenic.com/show_bug.cgi?id=4787. We disable replication
as a workaround.

  $ hgmo exec hgssh /set-mirrors.py

  $ hgmo create-repo users/user_example.com/repo-1 1
  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1

Mark repo as non-publishing
  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 3
  > EOF
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? Repository marked as non-publishing: draft changesets will remain in the draft phase when pushed.

Enable obsolescence on the repo

  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 5
  > EOF
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? Obsolescence is now enabled for this repository.
  
  Obsolescence is currently an experimental feature. It may be disabled at any
  time. Your obsolescence data may be lost at any time. You have been warned.
  
  Enjoy living on the edge.

Create initial repo content

  $ cd repo-1
  $ cat >> .hg/hgrc << EOF
  > [extensions]
  > rebase=
  > 
  > [experimental]
  > evolution=all
  > EOF

  $ touch foo
  $ hg -q commit -A -m initial
  $ touch bar
  $ hg -q commit -A -m bar
  $ hg -q up -r 0
  $ touch baz
  $ hg -q commit -A -m baz

  $ hg push -f
  pushing to ssh://*:$HGPORT/users/user_example.com/repo-1 (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 3 changesets with 3 changes to 3 files (+1 heads)
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  remote: replication to mirrors completed successfully in \d+.\ds (re)
  remote: 
  remote: View your changes here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/96ee1d7354c4
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/c7176a0c153e
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/316dccdaed3c
  $ cd ..

Create another clone

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1 repo-1-clone
  $ cat >> repo-1-clone/.hg/hgrc << EOF
  > [experimental]
  > evolution=all
  > EOF

Create some obsolescence markers

  $ cd repo-1
  $ hg rebase -s 1 -d 2
  rebasing 1:c7176a0c153e "bar"
  $ hg debugobsolete
  c7176a0c153ec7dd9c5aab8b6bc42d742d1ed1f4 d22031ed19ecc068e154a6c307c63adbb316dbb2 0 (* +0000) {'user': 'test'} (glob)

  $ hg push ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1
  pushing to ssh://*:$HGPORT/users/user_example.com/repo-1 (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 0 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  remote: replication to mirrors completed successfully in \d+.\ds (re)
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/d22031ed19ec
  remote: replication to mirrors completed successfully in \d+.\ds (re)
  $ cd ..

Pulling should get the obsmarkers

  $ cd repo-1-clone
  $ hg pull
  pulling from ssh://*:$HGPORT/users/user_example.com/repo-1 (glob)
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 0 changes to 1 files
  (run 'hg update' to get a working copy)
  $ hg debugobsolete
  c7176a0c153ec7dd9c5aab8b6bc42d742d1ed1f4 d22031ed19ecc068e154a6c307c63adbb316dbb2 0 (* +0000) {'user': 'test'} (glob)

  $ cd ..

  $ hgmo stop
