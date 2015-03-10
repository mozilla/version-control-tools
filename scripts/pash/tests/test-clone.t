#require docker

  $ . $TESTDIR/scripts/pash/tests/helpers.sh
  $ hgmoenv
  $ standarduser

  $ hgmo create-repo mozilla-central 3
  $ hgmo create-repo integration/mozilla-inbound 3
  $ hgmo create-repo hgcustom/version-controlt-tools 2

We should get a prompt saying we are creating a new user repo.
This also tests the exit choice.

  $ testuserssh $SSH_SERVER clone repo-1 << EOF
  > 0
  > EOF
  Warning: Permanently added '[*]:$HGPORT' (RSA) to the list of known hosts.\r (glob) (esc)
  Making repo %(repo)s for %(user)s.
  
  This repo will appear as hg.mozilla.org/users/user_example.com/repo-1s.
  
  If you need a top level repo, please quit now and file a
  Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed?  (no-eol)

  $ hgmo clean
