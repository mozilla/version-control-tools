#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser
  $ hgmo create-repo users/user_example.com/repo-1 scm_level_1
  (recorded repository creation in replication log)

  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 2
  > 1
  > This is my repo!
  > EOF
  Editing repo https://hg.mozilla.org/user_example.com/repo-1
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? You are about to edit the description for hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need to edit the description for a top level repo, please quit now
  and file a Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Enter a one line descripton for the repository:  (no-eol)

  $ hgmo exec hgssh cat /repo/hg/mozilla/users/user_example.com/repo-1/.hg/hgrc
  [web]
  description = This is my repo!
  

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 cat /repo/hg/mozilla/users/user_example.com/repo-1/.hg/hgrc
  [web]
  description = This is my repo!
  

Check the repo-config and repo-group commands work as intended.

  $ standarduserssh $SSH_SERVER repo-config users/user_example.com/repo-1
  [web]
  description = This is my repo!
  

  $ standarduserssh $SSH_SERVER repo-group users/user_example.com/repo-1
  scm_level_1


Check that multi-line inputs are handled correctly.

  $ export BADDESCRIPTION=`python -c "print('Description\\x0d[hooks]\\x0dpre-log=touch /tmp/blah')"`
  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 2
  > 1
  > $BADDESCRIPTION
  > EOF
  Editing repo https://hg.mozilla.org/user_example.com/repo-1
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? You are about to edit the description for hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need to edit the description for a top level repo, please quit now
  and file a Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Enter a one line descripton for the repository:  (no-eol)

  $ hgmo exec hgssh cat /repo/hg/mozilla/users/user_example.com/repo-1/.hg/hgrc
  [web]
  description = Description
  

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ hgmo exec hgweb0 cat /repo/hg/mozilla/users/user_example.com/repo-1/.hg/hgrc
  [web]
  description = Description
  
Check that disallowed characters are handled correctly.

  $ export BADDESCRIPTION=`python -c "print('Description\\tHi!')"`
  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 2
  > 1
  > $BADDESCRIPTION
  > EOF
  Editing repo https://hg.mozilla.org/user_example.com/repo-1
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? You are about to edit the description for hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need to edit the description for a top level repo, please quit now
  and file a Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Enter a one line descripton for the repository: 
  Description must contain only printable characters. (no-eol)
  [1]


Check that HTML characters are escaped correctly.

  $ export BADDESCRIPTION=`python -c "print('Hello! <a href=bad>')"`
  $ standarduserssh $SSH_SERVER edit repo-1 << EOF
  > 2
  > 1
  > $BADDESCRIPTION
  > EOF
  Editing repo https://hg.mozilla.org/user_example.com/repo-1
  
  0) Exit.
  1) Delete the repository.
  2) Edit the description.
  3) Mark repository as non-publishing.
  4) Mark repository as publishing.
  5) Enable obsolescence support (experimental).
  6) Disable obsolescence support.
  
  What would you like to do? You are about to edit the description for hg.mozilla.org/users/user_example.com/repo-1.
  
  If you need to edit the description for a top level repo, please quit now
  and file a Developer Services :: hg.mozilla.org bug at
  https://bugzilla.mozilla.org/enter_bug.cgi?product=Developer%20Services&component=Mercurial%3A%20hg.mozilla.org
  
  0) Exit.
  1) yes.
  2) no.
  
  Proceed? Enter a one line descripton for the repository:  (no-eol)

  $ hgmo exec hgssh cat /repo/hg/mozilla/users/user_example.com/repo-1/.hg/hgrc
  [web]
  description = Hello! &lt;a href=bad&gt;
  
  $ hgmo clean
