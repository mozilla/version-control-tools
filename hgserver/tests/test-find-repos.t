Create some repositories

  $ hg init has_hgrc
  $ cat >> has_hgrc/.hg/hgrc << EOF
  > [extensions]
  > prune =
  > EOF

  $ hg init upgradebackup
  $ mkdir upgradebackup/.hg/upgradebackup.asdfasdf/

  $ hg init no_requirement
  >>> with open('no_requirement/.hg/requires', 'r') as f:
  ...     reqs = f.read().splitlines()
  >>> reqs.remove('store')
  >>> with open('no_requirement/.hg/requires', 'w') as f:
  ...     f.write('\n'.join(reqs))

  $ hg init has_obsstore
  $ touch has_obsstore/.hg/store/obsstore

Search for various repositories

  $ find-hg-repos --hgrc .
  /has_hgrc
  $ find-hg-repos --requirement store .
  /has_hgrc
  /has_obsstore
  /upgradebackup
  $ find-hg-repos --no-requirement store .
  /no_requirement
  $ find-hg-repos --upgrade-backup .
  /upgradebackup
  $ find-hg-repos --obsstore .
  /has_obsstore
  $ find-hg-repos --group $USER .
  /has_hgrc
  /has_obsstore
  /no_requirement
  /upgradebackup
