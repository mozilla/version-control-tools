  $ . $TESTDIR/hgext/configwizard/tests/helpers.sh

#if sslcontext hg39
Modern Mercurial doesn't need to pin fingerprints

  $ hg --config configwizard.steps=security,configchange configwizard
  This wizard will guide you through configuring Mercurial for an optimal
  experience contributing to Mozilla projects.
  
  The wizard makes no changes without your permission.
  
  To begin, press the enter/return key.
   <RETURN>
#endif

#if no-sslcontext no-hg39
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
  +hg.mozilla.org = 73:7f:ef:ab:68:0f:49:3f:88:91:f0:b7:06:69:fd:8f:f2:55:c9:56
  +bitbucket.org = 3f:d3:c5:17:23:3c:cd:f5:2d:17:76:06:93:7e:ee:97:42:21:14:aa
  +bugzilla.mozilla.org = 7c:7a:c4:6c:91:3b:6b:89:cf:f2:8c:13:b8:02:c4:25:bd:1e:25:17

  Write changes to hgrc file (Yn)?  y

#endif

#if no-sslcontext hg39
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
  +hg.mozilla.org:fingerprints = sha256:8e:ad:f7:6a:eb:44:06:15:ed:f3:e4:69:a6:64:60:37:2d:ff:98:88:37:bf:d7:b8:40:84:01:48:9c:26:ce:d9
  +bitbucket.org:fingerprints = sha256:4e:65:3e:76:0f:81:59:85:5b:50:06:0c:c2:4d:3c:56:53:8b:83:3e:9b:fa:55:26:98:9a:ca:e2:25:03:92:47
  +bugzilla.mozilla.org:fingerprints = sha256:95:BA:0F:F2:C4:28:75:9D:B5:DB:4A:50:5F:29:46:A3:A9:4E:1B:56:A5:AE:10:50:C3:DD:3A:AC:73:BF:4A:D9

  Write changes to hgrc file (Yn)?  y

#endif

#if no-hg39
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
  +hg.mozilla.org = 73:7f:ef:ab:68:0f:49:3f:88:91:f0:b7:06:69:fd:8f:f2:55:c9:56
  
  Write changes to hgrc file (Yn)?  y

#endif

#if hg39
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
  +hg.mozilla.org:fingerprints = sha256:8e:ad:f7:6a:eb:44:06:15:ed:f3:e4:69:a6:64:60:37:2d:ff:98:88:37:bf:d7:b8:40:84:01:48:9c:26:ce:d9
  
  Write changes to hgrc file (Yn)?  y


#endif
