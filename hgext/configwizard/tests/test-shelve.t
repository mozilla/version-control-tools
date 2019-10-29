  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting shelve doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=shelve,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable the shelve feature. Equivalent to git stash (Yn)  n

No prompt if shelve already enabled

  $ hg --config configwizard.steps=shelve --config extensions.shelve= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

shelve extension enabled if no input

  $ hg --config configwizard.steps=shelve,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable the shelve feature. Equivalent to git stash (Yn)  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +shelve =
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  shelve = 
