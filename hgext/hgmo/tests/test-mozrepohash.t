  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > EOF

  $ hg init repo
  $ cd repo

Empty repo is hashable

  $ hg mozrepohash
  normal: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  unfiltered: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  phases: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  pushlog: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  obsstore: 5d84b09c2a8ff32940e865afbdbdae4c677485c7e9ce36f84dcc98a23ae67ba9

Repo with single changeset has a hash

  $ echo 0 > foo
  $ hg -q commit -A -m initial
  $ hg mozrepohash
  normal: e038fa0a8990f29ea9066d94564af8408f46a0e7c8ab123131b1fee143534e32
  unfiltered: e038fa0a8990f29ea9066d94564af8408f46a0e7c8ab123131b1fee143534e32
  phases: bf9f494d166953d7e8d2ddc24d05c3cc6613af78a052cda5bef7a9e70926e493
  pushlog: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  obsstore: 5d84b09c2a8ff32940e865afbdbdae4c677485c7e9ce36f84dcc98a23ae67ba9

Changing the phase changes the hash

  $ hg phase --public -r .
  $ hg mozrepohash
  normal: e038fa0a8990f29ea9066d94564af8408f46a0e7c8ab123131b1fee143534e32
  unfiltered: e038fa0a8990f29ea9066d94564af8408f46a0e7c8ab123131b1fee143534e32
  phases: d78aadc55ac73d879f79532ec829d15d83cff06578d7d41250d090062329354e
  pushlog: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  obsstore: 5d84b09c2a8ff32940e865afbdbdae4c677485c7e9ce36f84dcc98a23ae67ba9

Adding a bookmark changes the hash

  $ hg book mymark
  $ hg mozrepohash
  normal: e038fa0a8990f29ea9066d94564af8408f46a0e7c8ab123131b1fee143534e32
  unfiltered: e038fa0a8990f29ea9066d94564af8408f46a0e7c8ab123131b1fee143534e32
  phases: d78aadc55ac73d879f79532ec829d15d83cff06578d7d41250d090062329354e
  pushlog: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  obsstore: 5d84b09c2a8ff32940e865afbdbdae4c677485c7e9ce36f84dcc98a23ae67ba9
