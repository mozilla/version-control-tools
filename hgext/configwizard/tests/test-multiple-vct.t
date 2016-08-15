  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

  $ if [ "${TESTDIR#*version-control-tools}" = "version-control-tools" ]; then exit 80; fi

Running multiple extensions from same v-c-t checkout works

  $ hg --config extensions.firefoxtree=$TESTDIR/hgext/firefoxtree --config configwizard.steps=multiplevct configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

Running extension from another v-c-t directory fails
(configwizard runs from a v-c-t checkout so it should trigger detection itself)

  $ mkdir -p a/version-control-tools/hgext/firefoxtree
  $ touch a/version-control-tools/hgext/firefoxtree/__init__.py

  $ hg --config extensions.firefoxtree=$TESTTMP/a/version-control-tools/hgext/firefoxtree --config configwizard.steps=multiplevct configwizard
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
  
