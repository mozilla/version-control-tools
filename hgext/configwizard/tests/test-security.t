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
  +hg.mozilla.org = 1c:a5:7d:a1:28:db:78:f6:52:4d:c0:e6:38:9b:08:43:ec:1f:ef:64
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
  +hg.mozilla.org:fingerprints = sha256:17:38:aa:92:0b:84:3e:aa:8e:52:52:e9:4c:2f:98:a9:0e:bf:6c:3e:e9:15:ff:0a:29:80:f7:06:02:5b:e8:48
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
  +hg.mozilla.org = 1c:a5:7d:a1:28:db:78:f6:52:4d:c0:e6:38:9b:08:43:ec:1f:ef:64
  
  Write changes to hgrc file (Yn)?  y

#endif

#if hg39
[hostfingerprints] deleted our fingerprints

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
  @@ -1,2 +1 @@
   [hostfingerprints]
  -hg.mozilla.org = aa:bb:cc:dd
  
  Write changes to hgrc file (Yn)?  y


#endif

#if hg39
Old hg.mozilla.org fingerprint in [hostsecurity] is deleted

  $ cat > .hgrc << EOF
  > [hostsecurity]
  > hg.mozilla.org:fingerprints = sha256:aa:bb:cc:dd
  > unrelated.host:fingerprints = sha256:aa:bb:cc:dd
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
  @@ -1,3 +1,2 @@
   [hostsecurity]
  -hg.mozilla.org:fingerprints = sha256:aa:bb:cc:dd
   unrelated.host:fingerprints = sha256:aa:bb:cc:dd
  
  Write changes to hgrc file (Yn)?  y

#endif
