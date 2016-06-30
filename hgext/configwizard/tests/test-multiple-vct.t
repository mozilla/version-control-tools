  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

  $ mkdir -p a/version-control-tools/hgext/firefoxtree
  $ mkdir -p b/version-control-tools/hgext/mozext

  $ touch a/version-control-tools/hgext/firefoxtree/__init__.py
  $ touch b/version-control-tools/hgext/mozext/__init__.py

  $ hg --config extensions.firefoxtree=$TESTTMP/a/version-control-tools/hgext/firefoxtree --config extensions.mozext=$TESTTMP/b/version-control-tools/hgext/mozext --config configwizard.steps=multiplevct configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  *** WARNING ***
  
  Multiple version-control-tools repositories are referenced in your
  Mercurial config. Extensions and other code within the
  version-control-tools repository could run with inconsistent results.
  
  Please manually edit the following file to reference a single
  version-control-tools repository:
  
      $TESTTMP/.hgrc
  
