  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting history editing doesn't enable extensions

  $ hg --config ui.interactive=true --config configwizard.steps=historyediting,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable history rewriting commands (Yn)?  n


No prompt if extensions already enabled

  $ hg --config configwizard.steps=historyediting --config extensions.histedit= --config extensions.rebase= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

histedit and rebase enabled when appropriate

  $ hg --config configwizard.steps=historyediting,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Enable history rewriting commands (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,3 @@
  +[extensions]
  +histedit =
  +rebase =
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  histedit = 
  rebase = 
