  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Should not get legacy version message when running on supported version

  $ cat > fakeversion.py << EOF
  > from mercurial import util
  > util.version = lambda: '4.2.3'
  > EOF

  $ FAKEVERSION='--config extensions.fakeversion=fakeversion.py'

  $ hg $FAKEVERSION --config configwizard.steps=hgversion configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>


Old version will print legacy message and prompt

  $ rm fakeversion.pyc
  $ cat >> fakeversion.py << EOF
  > util.version = lambda: '4.2.2'
  > EOF

  $ hg $FAKEVERSION --config configwizard.steps=hgversion configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  You are running an out of date Mercurial client (4.2.2).
  
  For a faster and better Mercurial experience, we HIGHLY recommend you
  upgrade.
  
  Legacy versions of Mercurial have known security vulnerabilities. Failure
  to upgrade may leave you exposed. You are highly encouraged to upgrade in
  case you aren't running a patched version.
  
  Please run `mach bootstrap` to upgrade your Mercurial install.
  
  Would you like to continue using an old Mercurial version (Yn)?  y

  $ hg --config ui.interactive=true --config configwizard.steps=hgversion $FAKEVERSION configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  You are running an out of date Mercurial client (4.2.2).
  
  For a faster and better Mercurial experience, we HIGHLY recommend you
  upgrade.
  
  Legacy versions of Mercurial have known security vulnerabilities. Failure
  to upgrade may leave you exposed. You are highly encouraged to upgrade in
  case you aren't running a patched version.
  
  Please run `mach bootstrap` to upgrade your Mercurial install.
  
  Would you like to continue using an old Mercurial version (Yn)?  n
  [1]


Too old version will fail outright

  $ rm fakeversion.pyc
  $ cat >> fakeversion.py << EOF
  > util.version = lambda: '3.4.2'
  > EOF

  $ hg $FAKEVERSION --config configwizard.steps=hgversion configwizard
  Your version of Mercurial (3.4) is too old to run `hg configwizard`.
  
  Mozilla's Mercurial support policy is to support at most the past
  1 year of Mercurial releases (or 4 major Mercurial releases).
  
  Please upgrade to Mercurial 3.5 or newer and try again.
  
  See https://mozilla-version-control-tools.readthedocs.io/en/latest/hgmozilla/installing.html
  for Mozilla-tailored instructions for install Mercurial.
  abort: upgrade Mercurial then run again
  [255]
