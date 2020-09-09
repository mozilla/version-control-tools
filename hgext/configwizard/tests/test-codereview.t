  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Saying no to code review doesn't go through that part of wizard

  $ hg --config ui.interactive=true --config configwizard.steps=codereview,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Will you be submitting commits to Mozilla (Yn)?  n

User is directed to Phabricator documentation if they are committing to Mozilla

  $ hg --config configwizard.steps=codereview,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Will you be submitting commits to Mozilla (Yn)?  y
  Commits to Mozilla projects are sent to Phabricator for review. To submit changes
  to Phabricator you should use the `moz-phab` tool, which supports Mozilla workflows.
  
  You can install `moz-phab` by running the following command after bootstrap:
      $ ./mach install-moz-phab
  
  More information and a user guide to Mozilla Phabricator can be found here:
      http://moz-conduit.readthedocs.io/en/latest/phabricator-user.html
  
  
