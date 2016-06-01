  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting pushtotry doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=pushtotry,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The push-to-try extension generates a temporary commit with a given
  try syntax and pushes it to the try server. The extension is intended
  to be used in concert with other tools generating try syntax so that
  they can push to try without depending on mq or other workarounds.
  
  (Relevant config option: extensions.push-to-try)
  
  Would you like to activate push-to-try (Yn)?  n

No prompt if extensions already enabled

  $ hg --config configwizard.steps=pushtotry --config extensions.push-to-try=$TESTDIR/hgext/push-to-try configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

push-to-try enabled when requested

  $ hg --config configwizard.steps=pushtotry,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The push-to-try extension generates a temporary commit with a given
  try syntax and pushes it to the try server. The extension is intended
  to be used in concert with other tools generating try syntax so that
  they can push to try without depending on mq or other workarounds.
  
  (Relevant config option: extensions.push-to-try)
  
  Would you like to activate push-to-try (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +push-to-try = */hgext/push-to-try (glob)
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  push-to-try = */hgext/push-to-try (glob)
