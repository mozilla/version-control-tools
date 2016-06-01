  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

  $ mkdir -p version-control-tools/hgext/firefoxtree
  $ touch version-control-tools/hgext/firefoxtree/__init__.py

  $ hg --config extensions.firefoxtree=$TESTTMP/version-control-tools/hgext/firefoxtree --config configwizard.steps=multiplevct configwizard
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
  
