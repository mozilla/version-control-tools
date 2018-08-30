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

No prompt if extensions already enabled

TRACKING hg45 4.4 didn't iterate sections in deterministic order. So we include
mozilla.ircnick twice.

  $ hg --config configwizard.steps=codereview --config extensions.reviewboard=$TESTDIR/hgext/reviewboard/client.py configwizard
  devel-warn: extension 'reviewboard' overwrite config item 'mozilla.ircnick' at: * (glob) (?)
  devel-warn: extension 'reviewboard' overwrite config item 'bugzilla.apikey' at: * (glob) (?)
  devel-warn: extension 'reviewboard' overwrite config item 'bugzilla.username' at: * (glob) (?)
  devel-warn: extension 'reviewboard' overwrite config item 'mozilla.ircnick' at: * (glob) (?)
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

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
  
