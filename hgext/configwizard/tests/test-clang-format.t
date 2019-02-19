  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting clang-format doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=clang-format,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "clang-format" extension provides execution of clang-format at the commit steps.
  It relies on ./mach clang-format directly.
  Would you like to activate clang-format (Yn)?  n

No prompt if extensions already enabled

  $ hg --config configwizard.steps=clang-format --config extensions.clang-format=$TESTDIR/hgext/clang-format configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

clang-format enabled when requested

  $ hg --config configwizard.steps=clang-format,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "clang-format" extension provides execution of clang-format at the commit steps.
  It relies on ./mach clang-format directly.
  Would you like to activate clang-format (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +clang-format = */hgext/clang-format (glob)
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  clang-format = */hgext/clang-format (glob)
