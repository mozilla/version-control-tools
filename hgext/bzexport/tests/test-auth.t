  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > mq =
  > bzexport = $TESTDIR/hgext/bzexport
  > 
  > [bzexport]
  > api_server = http://dummy/bzapi/
  > bugzilla = http://dummy/
  > EOF

Dummy out profiles directory to prevent running system from leaking in

  $ export FIREFOX_PROFILES_DIR=`pwd`

  $ hg init repo
  $ cd repo
  $ touch foo
  $ hg -q commit -A -m initial

No auth info should lead to prompting (verifies mozhg.auth is hooked up)

  $ hg newbug --product TestProduct --component TestComponent -t 'No auth' 'dummy'
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]

bzexport.username is deprecated and should print a warning

  $ hg --config bzexport.username=olduser newbug --product TestProduct --component TestComponent -t 'old username' 'dummy'
  (the bzexport.username config option is deprecated and ignored; use bugzilla.username instead)
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]

bzexport.password is deprecated and should print a warning

  $ hg --config bzexport.password=oldpass newbug --product TestProduct --component TestComponent -t 'old password' 'dummy'
  (the bzexport.password config option is deprecated and ignored; use bugzilla.password or cookie auth by logging into Bugzilla in Firefox)
  Bugzilla username: None
  abort: unable to obtain Bugzilla authentication.
  [255]
