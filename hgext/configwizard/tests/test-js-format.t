  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting js-format doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=js-format,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "js-format" extension provides execution of eslint+prettier at the commit steps.
  It relies on ./mach eslint --fix directly.
  Would you like to activate js-format (Yn)?  n

No prompt if extensions already enabled

  $ hg --config configwizard.steps=js-format --config extensions.js-format=$TESTDIR/hgext/js-format configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

js-format enabled when requested

  $ hg --config configwizard.steps=js-format,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "js-format" extension provides execution of eslint+prettier at the commit steps.
  It relies on ./mach eslint --fix directly.
  Would you like to activate js-format (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +js-format = */hgext/js-format (glob)
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  js-format = */hgext/js-format (glob)
