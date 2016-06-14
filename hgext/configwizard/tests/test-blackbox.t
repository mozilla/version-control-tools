  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting blackbox doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=blackbox,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable logging of commands to help diagnose bugs and performance problems (Yn)  n

No prompt if blackbox already enabled

  $ hg --config configwizard.steps=blackbox --config extensions.blackbox= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

blackbox extension enabled if no input

  $ hg --config configwizard.steps=blackbox,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable logging of commands to help diagnose bugs and performance problems (Yn)  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +blackbox =
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  blackbox = 
