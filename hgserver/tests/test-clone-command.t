#require docker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central 3
  $ hgmo create-repo integration/mozilla-inbound 3
  $ hgmo create-repo hgcustom/version-control-tools 1

  $ hg -q clone ssh://$SSH_SERVER:$HGPORT/hgcustom/version-control-tools vct
  $ cd vct
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://*:$HGPORT/hgcustom/version-control-tools (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/hgcustom/version-control-tools/rev/96ee1d7354c4
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
  1) 
  2) hgcustom/version-control-tools
  3) integration/mozilla-inbound
  4) mozilla-central
  
  Pick a source repo:  (no-eol)

Selecting a repo will result in a prompt

  $ standarduserssh $SSH_SERVER clone repo-1 << EOF
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
  1) 
  2) hgcustom/version-control-tools
  3) integration/mozilla-inbound
  4) mozilla-central
  
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
  > 2
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
  1) 
  2) hgcustom/version-control-tools
  3) integration/mozilla-inbound
  4) mozilla-central
  
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
  > 2
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
  1) 
  2) hgcustom/version-control-tools
  3) integration/mozilla-inbound
  4) mozilla-central
  
  Pick a source repo: About to clone /hgcustom/version-control-tools to /users/user_example.com/repo-1
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Please do not interrupt this operation.
  Please wait.  Cloning /hgcustom/version-control-tools to /users/user_example.com/repo-1
  Clone complete.
  Fixing permissions, don't interrupt.
  Repository marked as non-publishing: draft changesets will remain in the draft phase when pushed.

We are able to clone from the newly-created repo

  $ hg clone ssh://$SSH_SERVER:$HGPORT/users/user_example.com/repo-1 user-repo-1
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

We are able to push to the new user repo

  $ cd user-repo-1
  $ echo commit2 > foo
  $ hg commit -m 'commit 2'
  $ hg push
  pushing to ssh://*:$HGPORT/users/user_example.com/repo-1 (glob)
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: Trying to insert into pushlog.
  remote: Inserted into the pushlog db successfully.
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/users/user_example.com/repo-1/rev/384b668fc3c2

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

  $ hgmo stop
