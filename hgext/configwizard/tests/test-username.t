  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

No user input should result in failure to set username

  $ hg --config configwizard.steps=username configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  You don't have a username defined in your Mercurial config file. In order
  to author commits, you'll need to define a name and e-mail address.
  
  This data will be publicly available when you send commits/patches to others.
  If you aren't comfortable giving us your full name, pseudonames are
  acceptable.
  
  (Relevant config option: ui.username)
  What is your name? 
  Unable to set username; You will be unable to author commits
  

Name but no email should result in failure to set username

  $ hg --config ui.interactive=true --config configwizard.steps=username configwizard << EOF
  >  
  > Joe Smith
  > 
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
  What is your name? Joe Smith
  What is your e-mail address? 
  Unable to set username; You will be unable to author commits
  
Name and email will result in ui.username being set

  $ hg --config ui.interactive=true --config configwizard.steps=username,configchange configwizard << EOF
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
   <RETURN>
  You don't have a username defined in your Mercurial config file. In order
  to author commits, you'll need to define a name and e-mail address.
  
  This data will be publicly available when you send commits/patches to others.
  If you aren't comfortable giving us your full name, pseudonames are
  acceptable.
  
  (Relevant config option: ui.username)
  What is your name? Joe Smith
  What is your e-mail address? jsmith@example.com
  setting ui.username=Joe Smith <jsmith@example.com>
  
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -0,0 +1,2 @@
  +[ui]
  +username = Joe Smith <jsmith@example.com>
  
  Write changes to hgrc file (Yn)?  y

  $ cat .hgrc
  [ui]
  username = Joe Smith <jsmith@example.com>
