  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

[hostfingerprints] not added on modern hg

  $ hg --config configwizard.steps=security,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>

#if no-sslcontext

  $ hg --config configwizard.steps=security,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.

  The wizard makes no changes without your permission.

  To begin, press the enter/return key.
   <RETURN>
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -1,1 +1,4 @@
  +[hostfingerprints]
  +hg.mozilla.org = af:27:b9:34:47:4e:e5:98:01:f6:83:2b:51:c9:aa:d8:df:fb:1a:27
  +bitbucket.org = 3f:d3:c5:17:23:3c:cd:f5:2d:17:76:06:93:7e:ee:97:42:21:14:aa
  +bugzilla.mozilla.org = 7c:7a:c4:6c:91:3b:6b:89:cf:f2:8c:13:b8:02:c4:25:bd:1e:25:17

  Write changes to hgrc file (Yn)?  y

#endif

fingerprints updated when they are already pinned

  $ cat > .hgrc << EOF
  > [hostfingerprints]
  > hg.mozilla.org = aa:bb:cc:dd
  > EOF

  $ hg --config configwizard.steps=security,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
  Your config file needs updating.
  Would you like to see a diff of the changes first (Yn)?  y
  --- hgrc.old
  +++ hgrc.new
  @@ -1,2 +1,4 @@
   [hostfingerprints]
  -hg.mozilla.org = aa:bb:cc:dd
  +hg.mozilla.org = af:27:b9:34:47:4e:e5:98:01:f6:83:2b:51:c9:aa:d8:df:fb:1a:27
  +bitbucket.org = 3f:d3:c5:17:23:3c:cd:f5:2d:17:76:06:93:7e:ee:97:42:21:14:aa
  +bugzilla.mozilla.org = 7c:7a:c4:6c:91:3b:6b:89:cf:f2:8c:13:b8:02:c4:25:bd:1e:25:17
  
  Write changes to hgrc file (Yn)?  y

