  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

  $ cat > fakeversion.py << EOF
  > from mercurial import util
  > util.version = lambda: '4.1.2'
  > EOF

Rejecting color doesn't enable it

  $ hg --config extensions.fakeversion=fakeversion.py --config ui.interactive=true --config configwizard.steps=color,configchange configwizard << EOF
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

  $ hg --config extensions.fakeversion=fakeversion.py --config configwizard.steps=color --config extensions.color= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

color extension enabled if no input

  $ hg --config extensions.fakeversion=fakeversion.py --config configwizard.steps=color,configchange configwizard
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

#if hg42

Color extension removed in Mercurial 4.2+

  $ hg --config configwizard.steps=color,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Removing extensions.color because color is enabled by default in Mercurial 4.2+
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -1,2 +1 @@
   [extensions]
  -color =
  
  Write changes to hgrc file (Yn)?  y

No prompt to enable color extension on 4.2+

  $ hg --config configwizard.steps=color,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

#endif
