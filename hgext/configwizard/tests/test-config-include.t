  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

A config file with %include has its included content parsed

  $ cat > .hgrc << EOF
  > [ui]
  > biz = baz
  > # precomment
  > %include hgrc.include
  > # postcomment
  > EOF

  $ cat > hgrc.include << EOF
  > [ui]
  > username = Joe <joe@example.com>
  > EOF

  $ HGRCPATH=.hgrc hg --config configwizard.steps=username,configchange --config extensions.configwizard=$TESTDIR/hgext/configwizard configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

%include is preserved when config written out again

  $ cat > hgrc.include << EOF
  > [ui]
  > foo=bar
  > EOF

  $ HGRCPATH=.hgrc hg --config ui.interactive=true --config configwizard.steps=username,configchange --config extensions.configwizard=$TESTDIR/hgext/configwizard configwizard << EOF
  > 
  > Joe Smith
  > jsmith@example.com
  > y
  > y
  > EOF
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   You don't have a username defined in your Mercurial config file. In order
  to author commits, you'll need to define a name and e-mail address.
  
  This data will be publicly available when you send commits/patches to others.
  If you aren't comfortable giving us your full name, pseudonames are
  acceptable.
  
  (Relevant config option: ui.username)
  What is your name? What is your e-mail address? setting ui.username=Joe Smith <jsmith@example.com>
  
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  --- hgrc.old
  +++ hgrc.new
  @@ -1,5 +1,6 @@
   [ui]
   biz = baz
  +username = Joe Smith <jsmith@example.com>
   # precomment
   %include hgrc.include
   # postcomment
  
  Write changes to hgrc file (Yn)?   (no-eol)

  $ cat .hgrc
  [ui]
  biz = baz
  username = Joe Smith <jsmith@example.com>
  # precomment
  %include hgrc.include
  # postcomment
