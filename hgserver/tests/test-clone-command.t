#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central scm_level_3
  (recorded repository creation in replication log)
  $ hgmo create-repo integration/mozilla-inbound scm_level_3
  (recorded repository creation in replication log)
  $ hgmo create-repo hgcustom/version-control-tools scm_level_1
  (recorded repository creation in replication log)

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/hgcustom/version-control-tools vct
  $ cd vct
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/hgcustom/version-control-tools
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/hgcustom/version-control-tools/rev/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  remote: recorded changegroup in replication log in \d+\.\d+s (re)
  $ cd ..

We should get a prompt saying we are creating a new user repo.
This also tests the exit choice.

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
  > 0
  > EOF
  Making repo repo-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed?  (no-eol)

Choosing "no" should have the same effect as exiting

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
  > 2
  > EOF
  Making repo repo-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed?  (no-eol)

Choosing "yes" will prompt us how to create the new repo

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
  > 1
  > 0
  > EOF
  Making repo repo-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? You can clone an existing public repo or a users private repo.
  You can also create an empty repository.
  
  0) Exit.
  1) Clone a public repository.
  2) Clone a private repository.
  3) Create an empty repository.
  
  Source repository:  (no-eol)

Cloning a public repo will show a list of existing repos

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
  > 1
  > 1
  > 0
  > EOF
  Making repo repo-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? You can clone an existing public repo or a users private repo.
  You can also create an empty repository.
  
  0) Exit.
  1) Clone a public repository.
  2) Clone a private repository.
  3) Create an empty repository.
  
  Source repository: We have the repo_list
  List of available public repos
  
  0) Exit.
  1) hgcustom/version-control-tools
  2) integration/mozilla-inbound
  3) mozilla-central
  
  Pick a source repo:  (no-eol)

Selecting a repo will result in a prompt

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
  > 1
  > 1
  > 1
  > 0
  > EOF
  Making repo repo-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? You can clone an existing public repo or a users private repo.
  You can also create an empty repository.
  
  0) Exit.
  1) Clone a public repository.
  2) Clone a private repository.
  3) Create an empty repository.
  
  Source repository: We have the repo_list
  List of available public repos
  
  0) Exit.
  1) hgcustom/version-control-tools
  2) integration/mozilla-inbound
  3) mozilla-central
  
  Pick a source repo: About to clone /hgcustom/version-control-tools to /users/user_example.com/repo-1
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed?  (no-eol)

Saying "no" is handled properly
(TODO this is buggy)

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
  > 1
  > 1
  > 1
  > 2
  > 0
  > EOF
  Making repo repo-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? You can clone an existing public repo or a users private repo.
  You can also create an empty repository.
  
  0) Exit.
  1) Clone a public repository.
  2) Clone a private repository.
  3) Create an empty repository.
  
  Source repository: We have the repo_list
  List of available public repos
  
  0) Exit.
  1) hgcustom/version-control-tools
  2) integration/mozilla-inbound
  3) mozilla-central
  
  Pick a source repo: About to clone /hgcustom/version-control-tools to /users/user_example.com/repo-1
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Fixing permissions, don't interrupt.
  Could not find repository at /users/user_example.com/repo-1.
  [1]

Saying "yes" to clone the repo will clone it.

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
  > 1
  > 1
  > 1
  > 1
  > EOF
  Making repo repo-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? You can clone an existing public repo or a users private repo.
  You can also create an empty repository.
  
  0) Exit.
  1) Clone a public repository.
  2) Clone a private repository.
  3) Create an empty repository.
  
  Source repository: We have the repo_list
  List of available public repos
  
  0) Exit.
  1) hgcustom/version-control-tools
  2) integration/mozilla-inbound
  3) mozilla-central
  
  Pick a source repo: About to clone /hgcustom/version-control-tools to /users/user_example.com/repo-1
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Please do not interrupt this operation.
  Please wait.  Cloning /hgcustom/version-control-tools to /users/user_example.com/repo-1
  Clone complete.
  Fixing permissions, don't interrupt.
  Repository marked as non-publishing: draft changesets will remain in the draft phase when pushed.

  $ hgmo exec hgssh grep generaldelta /repo/hg/mozilla/users/user_example.com/repo-1/.hg/requires
  generaldelta

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 cat /repo/hg/mozilla/users/user_example.com/repo-1/.hg/hgrc
  [phases]
  publish = False
  

  $ hgmo exec hgweb0 grep generaldelta /repo/hg/mozilla/users/user_example.com/repo-1/.hg/requires
  generaldelta

TODO build user WSGI file generation into replication system
  $ hgmo exec hgweb0 /usr/local/bin/make_user_wsgi_dirs.sh

We are able to clone from the newly-created repo

  $ hg clone ${HGWEB_0_URL}users/user_example.com/repo-1 user-repo-1
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 77538e1ce4be (hg44 !)
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

We are able to push to the new user repo

  $ cd user-repo-1
  $ echo commit2 > foo
  $ hg commit -m 'commit 2'
  $ hg push ssh://${SSH_SERVER}:${HGPORT}/users/user_example.com/repo-1
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/users/user_example.com/repo-1
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/72a8548a894aea3fd307e2b253e34df2b019da34
  remote: recorded changegroup in replication log in \d+\.\d+s (re)

  $ cd ..

TODO verify the new user repo shows up in hgweb

Specifying the source path when doing a clone command works

  $ standarduserssh $SSH_SERVER clone repo-2 hgcustom/version-control-tools
  Please wait.  Cloning /hgcustom/version-control-tools to /users/user_example.com/repo-2
  Clone complete.
  Fixing permissions, don't interrupt.
  Repository marked as non-publishing: draft changesets will remain in the draft phase when pushed.

TODO verify new user repo shows up in hgweb

Specifying an invalid source repo to clone will result in error
TODO this behavior is wrong (bug 758608)

  $ standarduserssh $SSH_SERVER clone repo-missing does-not-exist
  Sorry, there is no source repo called does-not-exist.
  
  If you think this is wrong, please file a Developer Services :: hg.mozilla.org
  bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  [1]

Attempting to create a user repo that already exists results in error

  $ standarduserssh $SSH_SERVER clone repo-2 hgcustom/version-control-tools
  You already have a repo called repo-2.
  
  If you think this is wrong, please file a Developer Services :: hg.mozilla.org
  bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  [1]

We can create a new empty repo

  $ standarduserssh $SSH_SERVER clone empty-1 << EOF
  > 1
  > 3
  > 1
  > EOF
  Making repo empty-1 for user@example.com.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/empty-1.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? You can clone an existing public repo or a users private repo.
  You can also create an empty repository.
  
  0) Exit.
  1) Clone a public repository.
  2) Clone a private repository.
  3) Create an empty repository.
  
  Source repository: About to create an empty repository at /users/user_example.com/empty-1
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Fixing permissions, don't interrupt.
  Repository marked as non-publishing: draft changesets will remain in the draft phase when pushed.

  $ hgmo exec hgssh grep generaldelta /repo/hg/mozilla/users/user_example.com/empty-1/.hg/requires
  generaldelta

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 cat /repo/hg/mozilla/users/user_example.com/empty-1/.hg/hgrc
  [phases]
  publish = False
  

  $ hgmo exec hgweb0 grep generaldelta /repo/hg/mozilla/users/user_example.com/empty-1/.hg/requires
  generaldelta

Cleanup

  $ hgmo clean
