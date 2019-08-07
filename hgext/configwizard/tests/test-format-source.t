  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

When not loading format-source we should not get the removal message.

  $ hg --config ui.interactive=true --config configwizard.steps=format-source configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
Remove extension when already enabled

  $ cat >> .hgrc << EOF
  > [extensions]
  > format-source = $TESTDIR/hgext/format-source
  > EOF

  $ hg --config configwizard.steps=format-source,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  
  Removing extensions.format-source since it's no longer needed. For the moment we
  want to disable format-source since the big format of Gecko has been performed.
  We will re-enable this when we will need it again.
  
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -1,2 +1 @@
   [extensions]
  -format-source = */hgext/format-source (glob)
  
  Write changes to hgrc file (Yn)?  y






  $ cat .hgrc
  [extensions]
