  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting color doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=color,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable color output to your terminal (Yn)  n


No prompt if color already enabled

  $ hg --config configwizard.steps=color --config extensions.color= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

color extension enabled if no input

  $ hg --config configwizard.steps=color,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable color output to your terminal (Yn)  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +color =
  
  Write changes to hgrc file (Yn)?  y
  $ cat .hgrc
  [extensions]
  color = 
