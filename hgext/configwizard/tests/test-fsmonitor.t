#require watchman

  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

  $ cat > fakeversion.py << EOF
  > from mercurial import util
  > util.version = lambda: '3.8.1'
  > EOF

Rejecting fsmonitor doesn't enable it

  $ hg --config extensions.fakeversion=fakeversion.py --config ui.interactive=true --config configwizard.steps=fsmonitor,configchange configwizard << EOF
  > 
  > n
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The fsmonitor extension integrates the watchman filesystem watching tool
  with Mercurial. Commands like `hg status`, `hg diff`, and `hg commit`
  (which need to examine filesystem state) can query watchman to obtain
  this state, allowing these commands to complete much quicker.
  
  When installed, the fsmonitor extension will automatically launch a
  background watchman daemon for accessed Mercurial repositories. It
  should "just work."
  
  Would you like to enable fsmonitor (Yn)?  n

#if hg38

No prompt if extensions already enabled

  $ hg --config configwizard.steps=fsmonitor --config extensions.fsmonitor= configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

#endif

fsmonitor enabled when requested

  $ hg --config extensions.fakeversion=fakeversion.py --config configwizard.steps=fsmonitor,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  The fsmonitor extension integrates the watchman filesystem watching tool
  with Mercurial. Commands like `hg status`, `hg diff`, and `hg commit`
  (which need to examine filesystem state) can query watchman to obtain
  this state, allowing these commands to complete much quicker.
  
  When installed, the fsmonitor extension will automatically launch a
  background watchman daemon for accessed Mercurial repositories. It
  should "just work."
  
  Would you like to enable fsmonitor (Yn)?  y
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[extensions]
  +fsmonitor =
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [extensions]
  fsmonitor = 
