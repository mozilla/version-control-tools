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

  $ hg --config configwizard.steps=codereview --config extensions.reviewboard=$TESTDIR/hgext/reviewboard/client.py configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

reviewboard is enabled when requested

  $ hg --config configwizard.steps=codereview,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Will you be submitting commits to Mozilla (Yn)?  y
  Commits to Mozilla projects are typically sent to MozReview. This is the
  preferred code review tool at Mozilla.
  
  Some still practice a legacy code review workflow that uploads patches
  to Bugzilla.
  
  1. MozReview only (preferred)
  2. Both MozReview and Bugzilla
  3. Bugzilla only
  
  Which code review tools will you be submitting code to?  1
  You do not have a Bugzilla API Key defined in your Mercurial config.
  
  In order to communicate with Bugzilla and services (like MozReview) that
  use Bugzilla for authentication, you'll need to supply an API Key.
  
  The Bugzilla API Key is optional. However, if you don't supply one,
  certain features may not work and/or you'll be prompted for one.
  
  You should only need to configure a Bugzilla API Key once.
  What is your Bugzilla email address? (optional) 
  Configure the "review" path so you can `hg push review` commits to Mozilla for review (Yn)?  y
  What is your IRC nick?  
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,4 @@
  +[extensions]
  +reviewboard = */hgext/reviewboard/client.py (glob)
  +[paths]
  +review = https://reviewboard-hg.mozilla.org/autoreview
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  reviewboard = */hgext/reviewboard/client.py (glob)
  [paths]
  review = https://reviewboard-hg.mozilla.org/autoreview

only bzexport can be enabled when requested

  $ hg --config ui.interactive=true --config configwizard.steps=codereview,configchange configwizard << EOF
  > 
  > y
  > 3
  > someone@example.com
  > apikey
  > y
  > mynick
  > y
  > y
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Will you be submitting commits to Mozilla (Yn)?  y
  Commits to Mozilla projects are typically sent to MozReview. This is the
  preferred code review tool at Mozilla.
  
  Some still practice a legacy code review workflow that uploads patches
  to Bugzilla.
  
  1. MozReview only (preferred)
  2. Both MozReview and Bugzilla
  3. Bugzilla only
  
  Which code review tools will you be submitting code to?  3
  You do not have a Bugzilla API Key defined in your Mercurial config.
  
  In order to communicate with Bugzilla and services (like MozReview) that
  use Bugzilla for authentication, you'll need to supply an API Key.
  
  The Bugzilla API Key is optional. However, if you don't supply one,
  certain features may not work and/or you'll be prompted for one.
  
  You should only need to configure a Bugzilla API Key once.
  What is your Bugzilla email address? (optional) someone@example.com
  Bugzilla API Keys can only be obtained through the Bugzilla web interface.
  
  Please perform the following steps:
  
    1) Open https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey
    2) Generate a new API Key
    3) Copy the generated key and paste it here
  Please enter a Bugzilla API Key: (optional) apikey
  Configure the "review" path so you can `hg push review` commits to Mozilla for review (Yn)?  y
  What is your IRC nick?  mynick
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -1,4 +1,10 @@
   [extensions]
   reviewboard = */hgext/reviewboard/client.py (glob)
  +bzexport = */hgext/bzexport (glob)
   [paths]
   review = https://reviewboard-hg.mozilla.org/autoreview
  +[mozilla]
  +ircnick = mynick
  +[bugzilla]
  +username = someone@example.com
  +apikey = apikey
  
  Write changes to hgrc file (Yn)?  y


  $ cat .hgrc
  [extensions]
  reviewboard = */hgext/reviewboard/client.py (glob)
  bzexport = */hgext/bzexport (glob)
  [paths]
  review = https://reviewboard-hg.mozilla.org/autoreview
  [mozilla]
  ircnick = mynick
  [bugzilla]
  username = someone@example.com
  apikey = apikey


Legacy credentials are removed from config file

  $ cat >> .hgrc << EOF
  > cookie = bzcookie
  > EOF

  $ hg --config ui.interactive=true --config bugzilla.cookie=cookie --config configwizard.steps=codereview,configchange configwizard << EOF
  > 
  > y
  > 3
  > someone2@example.com
  > apikey2
  > y
  > mynick
  > y
  > y
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Will you be submitting commits to Mozilla (Yn)?  y
  Commits to Mozilla projects are typically sent to MozReview. This is the
  preferred code review tool at Mozilla.
  
  Some still practice a legacy code review workflow that uploads patches
  to Bugzilla.
  
  1. MozReview only (preferred)
  2. Both MozReview and Bugzilla
  3. Bugzilla only
  
  Which code review tools will you be submitting code to?  3
  You do not have a Bugzilla API Key defined in your Mercurial config.
  
  In order to communicate with Bugzilla and services (like MozReview) that
  use Bugzilla for authentication, you'll need to supply an API Key.
  
  The Bugzilla API Key is optional. However, if you don't supply one,
  certain features may not work and/or you'll be prompted for one.
  
  You should only need to configure a Bugzilla API Key once.
  What is your Bugzilla email address? (optional) someone2@example.com
  Bugzilla API Keys can only be obtained through the Bugzilla web interface.
  
  Please perform the following steps:
  
    1) Open https://bugzilla.mozilla.org/userprefs.cgi?tab=apikey
    2) Generate a new API Key
    3) Copy the generated key and paste it here
  Please enter a Bugzilla API Key: (optional) apikey2
  Your existing Mercurial config uses a legacy method for defining Bugzilla
  credentials. Bugzilla API Keys are the most secure and preferred method
  for defining Bugzilla credentials. Bugzilla API Keys are also required
  if you have enabled 2 Factor Authentication in Bugzilla.
  
  For security reasons, the legacy credentials are being removed from the
  config.
  Configure the "review" path so you can `hg push review` commits to Mozilla for review (Yn)?  y
  What is your IRC nick?  mynick
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -6,6 +6,5 @@
   [mozilla]
   ircnick = mynick
   [bugzilla]
  -username = someone@example.com
  -apikey = apikey
  -cookie = bzcookie
  +username = someone2@example.com
  +apikey = apikey2
  
  Write changes to hgrc file (Yn)?  y
