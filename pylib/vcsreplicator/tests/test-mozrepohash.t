#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo repo scm_level_1
  (recorded repository creation in replication log)
  $ hgmo exec hgssh /set-hgrc-option repo phases publish False
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ standarduser
  $ hg -q clone ssh://$DOCKER_HOSTNAME:$HGPORT/repo
  $ cd repo

Empty repo is hashable

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 0
  total revisions: 0
  visible heads: 1
  total heads: 1
  normal repo hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  unfiltered repo hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  phases hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  heads hash: de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90
  unfiltered heads hash: de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90
  pushlog hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 0
  total revisions: 0
  visible heads: 1
  total heads: 1
  normal repo hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  unfiltered repo hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  phases hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  heads hash: de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90
  unfiltered heads hash: de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90
  pushlog hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855


Repo with single changeset has a hash

  $ echo 0 > foo
  $ hg -q commit -A -m initial
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/repo
  searching for changes
  remote: adding changesets
  remote: adding manifests
  remote: adding file changes
  remote: added 1 changesets with 1 changes to 1 files
  remote: recorded push in pushlog
  remote: 
  remote: View your change here:
  remote:   https://hg.mozilla.org/repo/rev/af1e0a150cd431eced63336021855fd2f59077f6
  remote: recorded changegroup in replication log in \d\.\d+s (re)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 1
  total revisions: 1
  visible heads: 1
  total heads: 1
  normal repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  unfiltered repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  phases hash: f82c49f1539afc1bf3b6fbddf9ade9d5ca944c99896fe05457ca0dd18e6d2aab
  heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  unfiltered heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  pushlog hash: * (glob)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 1
  total revisions: 1
  visible heads: 1
  total heads: 1
  normal repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  unfiltered repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  phases hash: f82c49f1539afc1bf3b6fbddf9ade9d5ca944c99896fe05457ca0dd18e6d2aab
  heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  unfiltered heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  pushlog hash: * (glob)

Changing the phase changes the hash

  $ hg phase --public -r .
  $ hg push
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/repo
  searching for changes
  no changes found
  remote: recorded updates to phases in replication log in \d\.\d+s (re)
  [1]


  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 1
  total revisions: 1
  visible heads: 1
  total heads: 1
  normal repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  unfiltered repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  phases hash: 044fcd295ebc79531e739260bd24b905c73c87dcac271dd816e5eb244ccfe14b
  heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  unfiltered heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  pushlog hash: * (glob)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 1
  total revisions: 1
  visible heads: 1
  total heads: 1
  normal repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  unfiltered repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  phases hash: 044fcd295ebc79531e739260bd24b905c73c87dcac271dd816e5eb244ccfe14b
  heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  unfiltered heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  pushlog hash: * (glob)

Adding a bookmark changes the hash

  $ hg book mymark
  $ hg push -B mymark
  pushing to ssh://$DOCKER_HOSTNAME:$HGPORT/repo
  searching for changes
  no changes found
  remote: recorded updates to bookmarks in replication log in \d\.\d+s (re)
  exporting bookmark mymark
  [1]

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag
  $ hgmo exec hgweb1 /var/hg/venv_replication/bin/vcsreplicator-consumer /etc/mercurial/vcsreplicator.ini --wait-for-no-lag

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 1
  total revisions: 1
  visible heads: 1
  total heads: 1
  normal repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  unfiltered repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  phases hash: 044fcd295ebc79531e739260bd24b905c73c87dcac271dd816e5eb244ccfe14b
  heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  unfiltered heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  pushlog hash: * (glob)

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/repo mozrepohash
  visible revisions: 1
  total revisions: 1
  visible heads: 1
  total heads: 1
  normal repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  unfiltered repo hash: b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28
  phases hash: 044fcd295ebc79531e739260bd24b905c73c87dcac271dd816e5eb244ccfe14b
  heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  unfiltered heads hash: e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c
  pushlog hash: * (glob)

Output can be formatted as JSON

  $ hgmo exec hgssh /var/hg/venv_tools/bin/hg -R /repo/hg/mozilla/repo mozrepohash -T json
  [
   {
    "heads": "e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c",
    "heads_total": 1,
    "heads_visible": 1,
    "normal": "b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28",
    "phases": "044fcd295ebc79531e739260bd24b905c73c87dcac271dd816e5eb244ccfe14b",
    "pushlog": "*", (glob)
    "revisions_total": 1,
    "revisions_visible": 1,
    "unfiltered": "b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28",
    "unfiltered_heads": "e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c"
   }
  ]

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/hg -R /repo/hg/mozilla/repo mozrepohash -T json
  [
   {
    "heads": "e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c",
    "heads_total": 1,
    "heads_visible": 1,
    "normal": "b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28",
    "phases": "044fcd295ebc79531e739260bd24b905c73c87dcac271dd816e5eb244ccfe14b",
    "pushlog": "*", (glob)
    "revisions_total": 1,
    "revisions_visible": 1,
    "unfiltered": "b801d81d6ddf2baf154b4abd5bad0750785131ee13c54ee7b207b5e2cacb2e28",
    "unfiltered_heads": "e5e0d912bf64df57c6ae45158322023f7a929afa10409041f457d7b90e971d4c"
   }
  ]
