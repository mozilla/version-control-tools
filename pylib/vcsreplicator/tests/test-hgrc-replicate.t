#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central 3
  (recorded repository creation in replication log)

hgrc file content is sent in a message

  $ hgmo exec hgssh /activate-hook mozilla-central dummy value
  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: hg-repo-init-1
    path: '{moz}/mozilla-central'
  - _created: \d+\.\d+ (re)
    content: '[hooks]
  
      dummy = value
  
  
      '
    name: hg-hgrc-update-1
    path: '{moz}/mozilla-central'

hgrc should have been written on client

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/hgrc
  [hooks]
  dummy = value
  

Replicating hgrc without hgrc file will delete file

  $ hgmo exec hgssh rm /repo/hg/mozilla/mozilla-central/.hg/hgrc
  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: hg-repo-init-1
    path: '{moz}/mozilla-central'
  - _created: \d+\.\d+ (re)
    content: '[hooks]
  
      dummy = value
  
  
      '
    name: hg-hgrc-update-1
    path: '{moz}/mozilla-central'
  - _created: \d+\.\d+ (re)
    content: null
    name: hg-hgrc-update-1
    path: '{moz}/mozilla-central'

  $ hgmo exec hgweb0 ls /repo/hg/mozilla/mozilla-central/.hg
  00changelog.i
  pushlog2.db
  requires
  store

Unicode in hgrc is preserved

  $ docker exec ${SSH_CID} /activate-hook mozilla-central dummy 'こんにちは'

  $ hgmo exec hgssh /repo/hg/venv_pash/bin/hg -R /repo/hg/mozilla/mozilla-central replicatehgrc
  recorded hgrc in replication log

  $ consumer --dump --partition 2
  - _created: \d+\.\d+ (re)
    name: hg-repo-init-1
    path: '{moz}/mozilla-central'
  - _created: \d+\.\d+ (re)
    content: '[hooks]
  
      dummy = value
  
  
      '
    name: hg-hgrc-update-1
    path: '{moz}/mozilla-central'
  - _created: \d+\.\d+ (re)
    content: null
    name: hg-hgrc-update-1
    path: '{moz}/mozilla-central'
  - _created: \d+\.\d+ (re)
    content: "[hooks]\ndummy = \u3053\u3093\u306B\u3061\u306F\n\n"
    name: hg-hgrc-update-1
    path: '{moz}/mozilla-central'

  $ hgmo exec hgweb0 cat /repo/hg/mozilla/mozilla-central/.hg/hgrc
  [hooks]
  dummy = \xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf (esc)
  

Cleanup

  $ hgmo stop
