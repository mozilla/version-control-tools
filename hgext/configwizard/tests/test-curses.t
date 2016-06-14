  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting curses doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=curses,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Mercurial can provide richer terminal interactions for some operations
  by using the popular "curses" library.
  
  Would you like to enable "curses" interfaces (Yn)?  n

No prompt if interface already set

  $ hg --config configwizard.steps=curses --config ui.interface=text configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

curses interfaces enabled

  $ hg --config configwizard.steps=curses,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Mercurial can provide richer terminal interactions for some operations
  by using the popular "curses" library.
  
  Would you like to enable "curses" interfaces (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[ui]
  +interface = curses
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [ui]
  interface = curses
