  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting pager doesn't enable it

  $ hg --config ui.interactive=true --config configwizard.steps=pager,configchange configwizard << EOF
  > 
  > 3
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "pager" extension transparently redirects command output to a pager
  program (like "less") so command output can be more easily consumed
  (e.g. output longer than the terminal can be scrolled).
  
  Please select one of the following for configuring pager:
  
    1. Enable pager and configure with recommended settings (preferred)
    2. Enable pager with default configuration
    3. Don't enable pager
  
  Which option would you like?  3

Can enable without configuring

  $ hg --config ui.interactive=true --config configwizard.steps=pager,configchange configwizard << EOF
  > 
  > 2
  > y
  > y
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "pager" extension transparently redirects command output to a pager
  program (like "less") so command output can be more easily consumed
  (e.g. output longer than the terminal can be scrolled).
  
  Please select one of the following for configuring pager:
  
    1. Enable pager and configure with recommended settings (preferred)
    2. Enable pager with default configuration
    3. Don't enable pager
  
  Which option would you like?  2
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +pager =
  
  Write changes to hgrc file (Yn)?  y

Configuring sets pager invocation and default attends list

  $ hg --config ui.interactive=true --config configwizard.steps=pager,configchange configwizard << EOF
  > 
  > 1
  > y
  > y
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "pager" extension transparently redirects command output to a pager
  program (like "less") so command output can be more easily consumed
  (e.g. output longer than the terminal can be scrolled).
  
  Please select one of the following for configuring pager:
  
    1. Enable pager and configure with recommended settings (preferred)
    2. Enable pager with default configuration
    3. Don't enable pager
  
  Which option would you like?  1
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -1,2 +1,8 @@
   [extensions]
   pager =
  +[pager]
  +pager = LESS=FRSXQ less
  +attend-help = true
  +attend-incoming = true
  +attend-outgoing = true
  +attend-status = true
  
  Write changes to hgrc file (Yn)?  y

No-op if everything is configured

  $ HGRCPATH=.hgrc hg --config extensions.configwizard=$TESTDIR/hgext/configwizard --config configwizard.steps=pager,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

less.less isn't changed if defined

  $ rm .hgrc
  $ hg --config ui.interactive=true --config configwizard.steps=pager,configchange --config pager.pager=less configwizard << EOF
  > 
  > 1
  > y
  > y
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "pager" extension transparently redirects command output to a pager
  program (like "less") so command output can be more easily consumed
  (e.g. output longer than the terminal can be scrolled).
  
  Please select one of the following for configuring pager:
  
    1. Enable pager and configure with recommended settings (preferred)
    2. Enable pager with default configuration
    3. Don't enable pager
  
  Which option would you like?  1
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,7 @@
  +[extensions]
  +pager =
  +[pager]
  +attend-help = true
  +attend-incoming = true
  +attend-outgoing = true
  +attend-status = true
  
  Write changes to hgrc file (Yn)?  y

new attend default is added

  $ cat > .hgrc << EOF
  > [extensions]
  > pager =
  > [pager]
  > attend-incoming = true
  > attend-outgoing = true
  > EOF

  $ hg --config ui.interactive=true --config configwizard.steps=pager,configchange --config pager.pager=less configwizard << EOF
  > 
  > 1
  > y
  > y
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The "pager" extension transparently redirects command output to a pager
  program (like "less") so command output can be more easily consumed
  (e.g. output longer than the terminal can be scrolled).
  
  Please select one of the following for configuring pager:
  
    1. Enable pager and configure with recommended settings (preferred)
    2. Enable pager with default configuration
    3. Don't enable pager
  
  Which option would you like?  1
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -3,3 +3,5 @@
   [pager]
   attend-incoming = true
   attend-outgoing = true
  +attend-help = true
  +attend-status = true
  
  Write changes to hgrc file (Yn)?  y
