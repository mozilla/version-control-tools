  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

File permissions of hgrc should be updated when group or all read perms are set

  $ touch .hgrc
  $ chmod 664 .hgrc

  $ hg --config configwizard.steps=configchange,permissions configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Your hgrc file is currently readable by others.
  
  Sensitive information such as your Bugzilla credentials could be
  stolen if others have access to this file/machine.
  
  Would you like to fix the file permissions (Yn)  y
  Changing permissions of $TESTTMP/.hgrc

  $ hg --config configwizard.steps=configchange,permissions configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
