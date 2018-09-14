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
  Commits to Mozilla projects are typically sent to Phabricator. This is the
  preferred code review tool at Mozilla.
  Phabricator installation instructions are here
  http://moz-conduit.readthedocs.io/en/latest/phabricator-user.html
  
