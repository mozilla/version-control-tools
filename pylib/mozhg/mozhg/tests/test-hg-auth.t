#require hg30+

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
  Bugzilla username: Bugzilla password: userid: None
  cookie: None
  username: user-i
  password: fakepass

If username and password are in config, they get used

  $ hg --config bugzilla.username=user1 --config bugzilla.password=pass1 bzauth
  userid: None
  cookie: None
  username: user1
  password: pass1

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
  Bugzilla username: userid: None
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
  > EOF

  $ mkdir profiles/foo

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

Custom bugzilla.url should be respected

  $ hg bzcreatecookie profiles/foo https://mybugzilla/ bzuser bzcookie
  $ hg --config bugzilla.url=https://mybugzilla/ bzauth
  userid: bzuser
  cookie: bzcookie
  username: None
  password: None

We don't need to test multiple profiles because the .py unit tests
should have that covered.
