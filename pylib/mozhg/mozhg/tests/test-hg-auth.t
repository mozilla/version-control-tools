#require hg31+

This test covers the logic in mozhg.auth.getbugzillauth() from a
generic Mercurial perspective.

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > bzauth = $TESTDIR/pylib/mozhg/mozhg/tests/auth.py
  > EOF

Dummy out the profiles directory to prevent running system from leaking in
  $ export FIREFOX_PROFILES_DIR=`pwd`

If nothing defined and not interactive, we get no auth

  $ hg bzauth
  Bugzilla username: None
  no auth

If nothing defined and not interactive and we require input, we should abort

  $ hg bzauth --require
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]

If nothing defined, we get prompted for username and password
  $ hg --config ui.interactive=true bzauth --fakegetpass fakepass << EOF
  > user-i
  > EOF
  Bugzilla username: user-i
  Bugzilla password: userid: None
  cookie: None
  username: user-i
  password: fakepass

If userid and cookie are in config, they get used

  $ hg --config bugzilla.userid=uid1 --config bugzilla.cookie=cookie1 bzauth
  userid: uid1
  cookie: cookie1
  username: None
  password: None

If username and password are in config, they get used

  $ hg --config bugzilla.username=user1 --config bugzilla.password=pass1 bzauth
  userid: None
  cookie: None
  username: user1
  password: pass1

If cookie and u/p are in config, we prefer the cookie

  $ hg --config bugzilla.username=user1 --config bugzilla.password=pass1 --config bugzilla.userid=uid1 --config bugzilla.cookie=cookie1 bzauth
  userid: uid1
  cookie: cookie1
  username: None
  password: None

If just username is in config, we get prompted for password

  $ hg --config ui.interactive=true --config bugzilla.username=justuser bzauth --fakegetpass justuserpass
  Bugzilla password: userid: None
  cookie: None
  username: justuser
  password: justuserpass

If just username and not interactive, we get no auth

  $ hg --config bugzilla.username=justusernoi bzauth
  no auth

If just password in config, we get prompted for username

  $ hg --config bugzilla.password=pass1 bzauth --config ui.interactive=true << EOF
  > justpass
  > EOF
  Bugzilla username: justpass
  userid: None
  cookie: None
  username: justpass
  password: pass1

Now we set up some Firefox profiles to test cookie extraction

  $ mkdir profiles
  $ export FIREFOX_PROFILES_DIR=`pwd`/profiles

  $ cat >> profiles/profiles.ini << EOF
  > [Profile0]
  > Name=foo
  > IsRelative=1
  > Path=foo
  > 
  > [Profile1]
  > Name=profile2
  > IsRelative=1
  > Path=profile2
  > EOF

  $ mkdir profiles/foo profiles/profile2

Empty profile should have no cookies and should get nothing

  $ hg bzauth
  Bugzilla username: None
  no auth

Profile with cookie from an unknown Bugzilla should get nothing

  $ hg bzcreatecookie profiles/foo http://dummy/ dummyuser dummypass
  $ hg bzauth
  Bugzilla username: None
  no auth

Profile with cookie from BMO should be returned

  $ hg bzcreatecookie profiles/foo https://bugzilla.mozilla.org/ bmouser bmocookie
  $ hg bzauth
  userid: bmouser
  cookie: bmocookie
  username: None
  password: None

If there is just a username specified in config, but we can find a profile with a cookie we should use the cookie.

  $ hg --config bugzilla.username=dontusethis bzauth
  userid: bmouser
  cookie: bmocookie
  username: None
  password: None

Custom bugzilla.url should be respected

  $ hg bzcreatecookie profiles/foo https://mybugzilla/ bzuser bzcookie
  $ hg --config bugzilla.url=https://mybugzilla/ bzauth
  userid: bzuser
  cookie: bzcookie
  username: None
  password: None

Requesting a specific profile works

  $ hg bzcreatecookie profiles/profile2 https://bugzilla.mozilla.org/ bmouser2 bmocookie2
  $ hg bzauth --ffprofile profile2
  userid: bmouser2
  cookie: bmocookie2
  username: None
  password: None

Specifying a profile via config option works

  $ cat >> profiles/profiles.ini << EOF
  > [Profile3]
  > Name=profile3
  > IsRelative=1
  > Path=profile3
  > EOF

  $ mkdir profiles/profile3
  $ hg bzcreatecookie profiles/profile3 https://bugzilla.mozilla.org/ bmouser3 bmocookie3

  $ hg --config bugzilla.firefoxprofile=profile3 bzauth
  userid: bmouser3
  cookie: bmocookie3
  username: None
  password: None

  $ hg --config bugzilla.firefoxprofile=profile2,profile3 bzauth
  userid: bmouser2
  cookie: bmocookie2
  username: None
  password: None

The default profile should be chosen over other profiles.

  $ cat >> profiles/profiles.ini << EOF
  > [Profile4]
  > Name=profile4
  > IsRelative=1
  > Path=profile4
  > Default=1
  > EOF

  $ mkdir profiles/profile4
  $ hg bzcreatecookie profiles/profile4 https://bugzilla.mozilla.org/ bmouser4 bmocookie4

  $ hg bzauth
  userid: bmouser4
  cookie: bmocookie4
  username: None
  password: None

But profile selection in config should override default.

  $ hg --config bugzilla.firefoxprofile=profile3 bzauth
  userid: bmouser3
  cookie: bmocookie3
  username: None
  password: None
