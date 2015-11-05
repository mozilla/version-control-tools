  $ hg init server
  $ cat > server/.hg/hgrc << EOF
  > [hooks]
  > changegroup.advertise_upgrade = python:mozhghooks.advertise_upgrade.hook
  > EOF

  $ hg -q clone --pull server client
  $ cd client
  $ touch foo
  $ hg -q commit -A -m initial

Modern hg with bundle2 doesn't see advertisement
#if hg35+
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Old client without bundle2 does
#else
  $ hg push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  YOU ARE PUSHING WITH AN OUT OF DATE MERCURIAL CLIENT!
  newer versions are faster and have numerous bug fixes
  upgrade instructions are at the following URL:
  https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmozilla/installing.html
#endif

Modern hg without bundle2 gets message
(this is a bit sub-optimal, but we should never see this in the wild, so
it's acceptable)

  $ echo bundle2disabled > foo
  $ hg commit -m 'bundle2 disabled'
  $ hg --config experimental.bundle2-exp=false push
  pushing to $TESTTMP/server
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  
  YOU ARE PUSHING WITH AN OUT OF DATE MERCURIAL CLIENT!
  newer versions are faster and have numerous bug fixes
  upgrade instructions are at the following URL:
  https://mozilla-version-control-tools.readthedocs.org/en/latest/hgmozilla/installing.html
