  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting tweakdefaults doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=tweakdefaults,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Mercurial has implemented some functionality behind ui.tweakdefaults config,
  that most users would like by default, but would break some workflows due to
  backwards compatibility issues.
  You can find more info here: https://www.mercurial-scm.org/wiki/FriendlyHGPlan
  
  Would you like to enable these features (Yn)?  n

No prompt if tweakdefaults already set

  $ hg --config configwizard.steps=tweakdefaults --config ui.tweakdefaults=true configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

Accepting prompt enables tweakdefaults

  $ hg --config configwizard.steps=tweakdefaults,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Mercurial has implemented some functionality behind ui.tweakdefaults config,
  that most users would like by default, but would break some workflows due to
  backwards compatibility issues.
  You can find more info here: https://www.mercurial-scm.org/wiki/FriendlyHGPlan
  
  Would you like to enable these features (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[ui]
  +tweakdefaults = true
  
  Write changes to hgrc file (Yn)?  y
 
  $ cat .hgrc
  [ui]
  tweakdefaults = true
