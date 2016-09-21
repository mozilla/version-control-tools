  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

#if sslcontext hg39+
Modern Mercurial doesn't need to pin fingerprints

  $ hg --config configwizard.steps=security,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
#endif

#if no-sslcontext no-hg39+
[hostfingerprints] get set on Mercurial <3.9 if modern SSL not supported

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

#if no-sslcontext hg39+
[hostsecurity] set on Mercurial 3.9+ when no modern SSL

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
  +[hostsecurity]
  +hg.mozilla.org:fingerprints = sha256:81:3d:75:69:e3:76:f8:5b:31:1e:92:c9:cf:56:23:f6:4b:c2:82:77:e3:63:fb:7f:28:65:d0:9a:88:fb:be:b7
  +bitbucket.org:fingerprints = sha256:4e:65:3e:76:0f:81:59:85:5b:50:06:0c:c2:4d:3c:56:53:8b:83:3e:9b:fa:55:26:98:9a:ca:e2:25:03:92:47
  +bugzilla.mozilla.org:fingerprints = sha256:10:95:a8:c1:e1:c3:18:fa:e4:95:40:99:11:07:6d:e3:79:ab:e5:b0:29:50:ff:40:e8:e8:63:c4:fd:f3:9f:cb

  Write changes to hgrc file (Yn)?  y

#endif

#if no-hg39+
[hostfingerprints] updated on Mercurial <3.9 when they are already pinned

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
  @@ -1,2 +1,2 @@
   [hostfingerprints]
  -hg.mozilla.org = aa:bb:cc:dd
  +hg.mozilla.org = af:27:b9:34:47:4e:e5:98:01:f6:83:2b:51:c9:aa:d8:df:fb:1a:27
  
  Write changes to hgrc file (Yn)?  y

#endif

#if hg39+
[hostfingerprints] deleted and converted to [hostsecurity]
(Note: no new fingerprints are added)

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
  @@ -1,2 +1,2 @@
  -[hostfingerprints]
  -hg.mozilla.org = aa:bb:cc:dd
  +[hostsecurity]
  +hg.mozilla.org:fingerprints = sha256:81:3d:75:69:e3:76:f8:5b:31:1e:92:c9:cf:56:23:f6:4b:c2:82:77:e3:63:fb:7f:28:65:d0:9a:88:fb:be:b7
  
  Write changes to hgrc file (Yn)?  y


#endif
