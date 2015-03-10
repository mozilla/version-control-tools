#require docker

  $ . $TESTDIR/scripts/pash/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central 3
  $ hgmo create-repo integration/mozilla-inbound 3
  $ hgmo create-repo hgcustom/version-control-tools 2

We should get a prompt saying we are creating a new user repo.
This also tests the exit choice.

  $ testuserssh $SSH_SERVER clone repo-1 << EOF
  > 0
  > EOF
  Warning: Permanently added '[*]:$HGPORT' (RSA) to the list of known hosts.\r (glob) (esc)
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

  $ testuserssh $SSH_SERVER clone repo-1 << EOF
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

  $ testuserssh $SSH_SERVER clone repo-1 << EOF
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

  $ testuserssh $SSH_SERVER clone repo-1 << EOF
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

  $ testuserssh $SSH_SERVER clone repo-1 << EOF
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

  $ hgmo clean
