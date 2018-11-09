  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting history editing doesn't enable extensions

  $ hg --config ui.interactive=true --config configwizard.steps=historyediting,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Various extensions provide functionality to rewrite repository history. These
  enable more powerful - and often more productive - workflows.
  
  If history rewriting is enabled, the following extensions will be enabled:
  
  absorb
     `hg absorb` automatically squashes/folds uncommitted changes in the working
     directory into the appropriate previous changeset. Learn more at
     https://gregoryszorc.com/blog/2018/11/05/absorbing-commit-changes-in-mercurial-4.8/.
  
  histedit
     `hg histedit` allows interactive editing of previous changesets. It presents
     you a list of changesets and allows you to pick actions to perform on each
     changeset. Actions include reordering changesets, dropping changesets,
     folding multiple changesets together, and editing the commit message for
     a changeset.
  
  rebase
     `hg rebase` allows re-parenting changesets from one "branch" of a DAG
     to another. The command is typically used to "move" changesets based on
     an older changeset to be based on the newest changeset.
  
  Would you like to enable these history editing extensions (Yn)?  n


No prompt if extensions already enabled

#if hg48
  $ hg --config configwizard.steps=historyediting --config extensions.absorb= --config extensions.histedit= --config extensions.rebase= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

#else
  $ hg --config configwizard.steps=historyediting --config extensions.histedit= --config extensions.rebase= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

#endif

absorb, histedit, and rebase enabled when appropriate

  $ hg --config configwizard.steps=historyediting,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Various extensions provide functionality to rewrite repository history. These
  enable more powerful - and often more productive - workflows.
  
  If history rewriting is enabled, the following extensions will be enabled:
  
  absorb
     `hg absorb` automatically squashes/folds uncommitted changes in the working
     directory into the appropriate previous changeset. Learn more at
     https://gregoryszorc.com/blog/2018/11/05/absorbing-commit-changes-in-mercurial-4.8/.
  
  histedit
     `hg histedit` allows interactive editing of previous changesets. It presents
     you a list of changesets and allows you to pick actions to perform on each
     changeset. Actions include reordering changesets, dropping changesets,
     folding multiple changesets together, and editing the commit message for
     a changeset.
  
  rebase
     `hg rebase` allows re-parenting changesets from one "branch" of a DAG
     to another. The command is typically used to "move" changesets based on
     an older changeset to be based on the newest changeset.
  
  Would you like to enable these history editing extensions (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,* @@ (glob)
  +[extensions]
  +absorb = (hg48 !)
  +histedit =
  +rebase =
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  absorb =  (hg48 !)
  histedit = 
  rebase = 
