  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

  $ mkdir $TESTTMP/evolve_test_dir
  $ export EVOLVETMP=$TESTTMP/evolve_test_dir

Rejecting evolve extension doesn't install and download

  $ hg --config ui.interactive=true --config configwizard.steps=evolve,configchange configwizard << EOF
  > <RETURN>
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  
  The evolve extension is a Mercurial extension for faster and
  safer mutable history. It implements the changeset evolution concept
  for Mercurial, allowing for safe and simple history re-writing. It
  includes some new commands such as fold, prune and amend which may
  improve your user experience with Mercurial.
  
  The evolve extension is recommended for working with Firefox repositories.
  More information about changeset evolution can be found by running:
  
    $ hg help evolution
  
  as well as:
  
    $ hg help -e evolve
  
  once the `evolve` extension is enabled.
  
  (Relevant config option: extensions.evolve)
  
  Would you like to enable the evolve extension? (Yn)  n


No prompt if extension enabled but not managed by the wizard

  $ hg --config configwizard.steps=evolve --config extensions.evolve="" configwizard
  *** failed to import extension evolve: No module named *evolve* (glob) (?)
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  
  WARNING: your copy of the evolve extension is not managed by this wizard.
  Please update evolve manually when upgrading your Mercurial version.
  
  To allow this wizard to manage evolve on your behalf, remove `evolve` from
  your hgrc files `extensions` section and re-run the wizard.


#if internet

Evolve repo cloned and enabled if requested

  $ hg --config mozilla.mozbuild_state_path="$EVOLVETMP" --config configwizard.steps=evolve,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  
  The evolve extension is a Mercurial extension for faster and
  safer mutable history. It implements the changeset evolution concept
  for Mercurial, allowing for safe and simple history re-writing. It
  includes some new commands such as fold, prune and amend which may
  improve your user experience with Mercurial.
  
  The evolve extension is recommended for working with Firefox repositories.
  More information about changeset evolution can be found by running:
  
    $ hg help evolution
  
  as well as:
  
    $ hg help -e evolve
  
  once the `evolve` extension is enabled.
  
  (Relevant config option: extensions.evolve)
  
  Would you like to enable the evolve extension? (Yn)  y
  adding changesets
  adding manifests
  adding file changes
  added \d+ changesets with \d+ changes to \d+ files (re)
  new changesets *:* (glob) (?)
  \d+ files updated, \d+ files merged, \d+ files removed, \d+ files unresolved (re)
  Evolve was downloaded successfully.
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +evolve = */evolve/hgext3rd/evolve (glob)
  
  Write changes to hgrc file (Yn)?  y
  $ cat .hgrc
  [extensions]
  evolve = */evolve/hgext3rd/evolve (glob)


Ensure evolve is installed by checking the evolve help entry

  $ HGRCPATH=.hgrc hg help -e evolve > /dev/null 2>&1

Do not pull if evolve enabled, in sibling directory to v-c-t (managed by wizard) and rejected prompt

  $ hg --config mozilla.mozbuild_state_path="$EVOLVETMP" --config ui.interactive=true --config configwizard.steps=evolve,configchange --config extensions.evolve=$EVOLVETMP/evolve/hgext3rd/evolve configwizard << EOF
  > <RETURN>
  > n
  > EOF
  pulling from https://repo.mercurial-scm.org/evolve/
  no changes found
  \d+ files updated, \d+ files merged, \d+ files removed, \d+ files unresolved (re)
  Evolve was updated successfully.
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>


Pull latest revision if evolve enabled, in sibling directory to v-c-t (managed by wizard) and confirmed prompt
Before doing so, strip a revision off the evolve directory to ensure a change is pulled.

  $ hg -R $EVOLVETMP/evolve --config extensions.strip= strip .
  \d+ files updated, \d+ files merged, \d+ files removed, \d+ files unresolved (re)
  saved backup bundle to * (glob)

  $ hg --config mozilla.mozbuild_state_path="$EVOLVETMP" --config extensions.evolve=$EVOLVETMP/evolve/hgext3rd/evolve --config configwizard.steps=evolve,configchange configwizard
  pulling from https://repo.mercurial-scm.org/evolve/
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  \d+ new obsolescence markers (re) (?)
  updating bookmark @
  added \d+ changesets with \d+ changes to \d+ files (re)
  new changesets *:* (glob)
  (run 'hg update' to get a working copy)
  \d+ files updated, \d+ files merged, \d+ files removed, \d+ files unresolved (re)
  Evolve was updated successfully.
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

Ensure evolve still works after pull by checking the help output

  $ HGRCPATH=.hgrc hg help -e evolve > /dev/null 2>&1


#endif
