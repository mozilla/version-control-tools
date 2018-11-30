  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

Rejecting smart-annotate doesn't install it

  $ hg --config ui.interactive=true --config configwizard.steps=smartannotate,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The ``hg smart-annotate`` command provides experimental support for
  viewing the annotate information while skipping certain changesets,
  such as code-formatting changes.
  
  Would you like to install the `hg smart-annotate` alias (Yn)?  n

Accepting smart-annotate installs it

  $ hg --config configwizard.steps=smartannotate,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The ``hg smart-annotate`` command provides experimental support for
  viewing the annotate information while skipping certain changesets,
  such as code-formatting changes.
  
  Would you like to install the `hg smart-annotate` alias (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,6 @@
  +[alias]
  +smart-annotate = annotate -w --skip ignored_changesets
  +[revsetalias]
  +ignored_changesets = desc("ignore-this-changeset") or extdata(get_ignored_changesets)
  +[extdata]
  +get_ignored_changesets = shell:cat `hg root`/.hg-annotate-ignore-revs 2> /dev/null || true
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [alias]
  smart-annotate = annotate -w --skip ignored_changesets
  [revsetalias]
  ignored_changesets = desc("ignore-this-changeset") or extdata(get_ignored_changesets)
  [extdata]
  get_ignored_changesets = shell:cat `hg root`/.hg-annotate-ignore-revs 2> /dev/null || true

Test that the command actually works. First set up the repo:

  $ hg init repo
  $ cd repo
  $ cat > foo.js << EOF
  > function foo(aBar) {
  >     aBar(); // call the functioN
  > }
  > EOF
  $ hg add foo.js
  $ hg -q commit -m "Initial commit"
  $ HGRCPATH=$TESTTMP/.hgrc hg annotate foo.js
  0: function foo(aBar) {
  0:     aBar(); // call the functioN
  0: }

Add more changesets. First using the ignore-this-changeset annotation

  $ cat > foo.js << EOF
  > function foo(aBar) {
  >     aBar(); // call the function
  > }
  > EOF
  $ hg -q commit -m "Fix typo # ignore-this-changeset"

Now using the .hg-annotate-ignore-revs

  $ cat > foo.js << EOF
  > function foo(bar) {
  >     bar(); // call the function
  > }
  > EOF
  $ hg -q commit -m "Change paramater style"
  $ hg log --rev tip --template="{node}\n" > .hg-annotate-ignore-revs
  $ hg add .hg-annotate-ignore-revs
  $ hg -q commit -m "Add .hg-annotate-ignore-revs file"

Now with just whitespace changes

  $ cat > foo.js << EOF
  > function foo(bar) {
  >   bar(); // call the function
  > }
  > EOF
  $ hg -q commit -m "Change whitespace style to 2 spaces"

And finally, verify that the output of annotate and smart-annotate is what is expected

  $ hg annotate foo.js
  2: function foo(bar) {
  4:   bar(); // call the function
  0: }
  $ HGRCPATH=$TESTTMP/.hgrc hg smart-annotate foo.js
  0* function foo(bar) {
  0*   bar(); // call the function
  0: }

Also verify that the revsetalias picks the two changesets

  $ HGRCPATH=$TESTTMP/.hgrc hg log --rev ignored_changesets --template="{desc|firstline}\n"
  Fix typo # ignore-this-changeset
  Change paramater style

