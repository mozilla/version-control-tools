  $ . $TESTDIR/hgext/firefoxreleases/tests/helpers.sh
  $ enable_extension

  $ hg init repo
  $ cd repo
  $ populate_simple_repo

firefoxrelease() revset should issue warning if feature not enabled

  $ hg log -r 'firefoxrelease()'
  (warning: firefoxrelease() revset not available)

  $ touch .hg/IS_FIREFOX_REPO
  $ hg log -r 'firefoxrelease()'
  (warning: firefoxrelease() revset not available)

And if the database is missing

  $ cat >> .hg/hgrc << EOF
  > [mozilla]
  > enablefirefoxreleases = true
  > EOF

  $ hg log -r 'firefoxrelease()'
  (warning: firefoxrelease() revset not available)

Empty set if database is empty

  $ touch .hg/firefoxreleases.db

  $ hg log -r 'firefoxrelease()'

Populate the database

  $ populate_simple_releases
  imported 3 builds

Revset should return data

  $ hg log -r 'firefoxrelease()' -T '{node|short} {desc}\n'
  94086d65796f commit 1
  dc94f7af4eda commit 2
  4e0f86874d25 commit 3

Can filter on platform

  $ hg log -r 'firefoxrelease(platform=win32)' -T '{node|short} {desc}\n'
  94086d65796f commit 1

Including multiple platforms

  $ hg log -r 'firefoxrelease(platform="win32 win64")' -T '{node|short} {desc}\n'
  94086d65796f commit 1
  dc94f7af4eda commit 2
