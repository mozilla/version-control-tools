  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting diff setting works

  $ hg --config ui.interactive=true --config configwizard.steps=diff,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Mercurial is not configured to produce diffs in a more readable format.
  
  Would you like to change this (Yn)?  n


diff.git and diff.showfunc should be enabled

  $ hg --config configwizard.steps=diff,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Mercurial is not configured to produce diffs in a more readable format.
  
  Would you like to change this (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,3 @@
  +[diff]
  +git = true
  +showfunc = true
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [diff]
  git = true
  showfunc = true

Should no-op when diff settings already optimal

  $ hg --config diff.git=1 --config diff.showfunc=1 --config configwizard.steps=diff,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
