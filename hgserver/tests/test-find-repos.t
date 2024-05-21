Create some repositories

  $ hg init has_hgrc
  $ cat >> has_hgrc/.hg/hgrc << EOF
  > [extensions]
  > prune =
  > EOF

  $ hg init upgradebackup
  $ mkdir upgradebackup/.hg/upgradebackup.asdfasdf/

  $ hg init no_requirement
  $ requires=$(grep -v '^store$' < no_requirement/.hg/requires)
  $ echo "$requires" > no_requirement/.hg/requires
  $ if [ -f no_requirement/.hg/store/requires ]; then
  >   requires=$(grep -v '^store$' < no_requirement/.hg/store/requires)
  >   echo "$requires" > no_requirement/.hg/store/requires
  > fi

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
