#require hgmodocker vcsreplicator

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 0 offset 0
  $ consumer --onetime
  vcsreplicator.consumer processing hg-repo-init-2: (repo: {moz}/mozilla-central) from partition 2 offset 0
  vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 1
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 2
  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['77538e1ce4be']) from partition 2 offset 3
  vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r77538e1ce4bec5f7aac58a7ceca2da0e38e90a72 -- ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > adding file changes
  vcsreplicator.consumer   > added 1 changesets with 1 changes to 1 files
  vcsreplicator.consumer   > new changesets 77538e1ce4be
  vcsreplicator.consumer   > (run 'hg update' to get a working copy)
  vcsreplicator.consumer   [0]
  vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central
  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/mozilla-central, heads: ['77538e1ce4be'], last_push_id: 1) from partition 2 offset 4

Corrupt the local repo

  $ echo corrupt > $TESTTMP/repos/mozilla-central/.hg/store/00manifest.i

  $ echo corrupt > foo
  $ hg commit -m 'push after mirror corrupted'
  $ hg -q push

  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 5
  $ consumer --onetime
  vcsreplicator.consumer processing heartbeat-1 from partition 2 offset 6

Pulling into corrupt repo should result in abort

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    heads:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    heads:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    last_push_id: 2
    name: hg-heads-1
    path: '{moz}/mozilla-central'

  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['0c6b2090d458']) from partition 2 offset 7
  vcsreplicator.consumer pulling 1 heads (0c6b2090d458675af812e445c8ab9b809e321f57) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r0c6b2090d458675af812e445c8ab9b809e321f57 -- ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > transaction abort!
  vcsreplicator.consumer   > rollback completed
  vcsreplicator.consumer   > abort: unknown version (29298) in revlog 00manifest
  vcsreplicator.consumer   [255]
  vcsreplicator.consumer exiting main consume loop with error
  Traceback (most recent call last):
    File "*/bin/vcsreplicator-consumer", line *, in <module> (glob)
      sys.exit(load_entry_point('vcsreplicator', 'console_scripts', 'vcsreplicator-consumer')())
    File "*/vcsreplicator/consumer.py", line *, in consumer_cli (glob)
      run_cli(handle_message_main)
    File "*/vcsreplicator/consumer.py", line *, in run_cli (glob)
      timeout=poll_timeout, (?)
      consume( (?)
    File "*/vcsreplicator/consumer.py", line *, in consume (glob)
      message_handler(config, payload)
    File "*/vcsreplicator/consumer.py", line *, in filterwrapper (glob)
      return message_handler(config, payload)
    File "/app/vct/pylib/vcsreplicator/vcsreplicator/consumer.py", line 184, in autorecoverwrapper
      raise err
    File "/app/vct/pylib/vcsreplicator/vcsreplicator/consumer.py", line 180, in autorecoverwrapper
      return message_handler(config, payload)
    File "*/vcsreplicator/consumer.py", line *, in handle_message_main (glob)
      payload["heads"], (?)
      return process_hg_changegroup( (?)
    File "*/vcsreplicator/consumer.py", line *, in process_hg_changegroup (glob)
      raise hglib.error.CommandError(args, res, out, err)
  hglib.error.CommandError: (255, b'pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central\nsearching for changes\nadding changesets\nadding manifests', b'transaction abort!\nrollback completed\nabort: unknown version (29298) in revlog 00manifest')
  [1]

And the message should still be not consumed

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    heads:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    name: hg-changegroup-2
    nodecount: 1
    path: '{moz}/mozilla-central'
    source: serve
  - _created: \d+\.\d+ (re)
    heads:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    last_push_id: 2
    name: hg-heads-1
    path: '{moz}/mozilla-central'

We should get the same failure if we try again

  $ consumer --onetime
  vcsreplicator.consumer processing hg-changegroup-2: (repo: {moz}/mozilla-central, heads: ['0c6b2090d458']) from partition 2 offset 7
  vcsreplicator.consumer pulling 1 heads (0c6b2090d458675af812e445c8ab9b809e321f57) and 1 nodes from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central
  vcsreplicator.consumer   $ hg pull -r0c6b2090d458675af812e445c8ab9b809e321f57 -- ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central
  vcsreplicator.consumer   > searching for changes
  vcsreplicator.consumer   > adding changesets
  vcsreplicator.consumer   > adding manifests
  vcsreplicator.consumer   > transaction abort!
  vcsreplicator.consumer   > rollback completed
  vcsreplicator.consumer   > abort: unknown version (29298) in revlog 00manifest
  vcsreplicator.consumer   [255]
  vcsreplicator.consumer exiting main consume loop with error
  Traceback (most recent call last):
    File "*/bin/vcsreplicator-consumer", line *, in <module> (glob)
      sys.exit(load_entry_point('vcsreplicator', 'console_scripts', 'vcsreplicator-consumer')())
    File "*/vcsreplicator/consumer.py", line *, in consumer_cli (glob)
      run_cli(handle_message_main)
    File "*/vcsreplicator/consumer.py", line *, in run_cli (glob)
      timeout=poll_timeout, (?)
      consume( (?)
    File "*/vcsreplicator/consumer.py", line *, in consume (glob)
      message_handler(config, payload)
    File "*/vcsreplicator/consumer.py", line *, in filterwrapper (glob)
      return message_handler(config, payload)
    File "/app/vct/pylib/vcsreplicator/vcsreplicator/consumer.py", line 184, in autorecoverwrapper
      raise err
    File "/app/vct/pylib/vcsreplicator/vcsreplicator/consumer.py", line 180, in autorecoverwrapper
      return message_handler(config, payload)
    File "*/vcsreplicator/consumer.py", line *, in handle_message_main (glob)
      payload["heads"], (?)
      return process_hg_changegroup( (?)
    File "*/vcsreplicator/consumer.py", line *, in process_hg_changegroup (glob)
      raise hglib.error.CommandError(args, res, out, err)
  hglib.error.CommandError: (255, b'pulling from ssh://$DOCKER_HOSTNAME:$HGPORT/mozilla-central\nsearching for changes\nadding changesets\nadding manifests', b'transaction abort!\nrollback completed\nabort: unknown version (29298) in revlog 00manifest')
  [1]

We can skip over the message

  $ consumer --skip
  skipped message in partition 2 for group ttest

  $ consumer --onetime
  vcsreplicator.consumer processing hg-heads-1: (repo: {moz}/mozilla-central, heads: ['0c6b2090d458'], last_push_id: 2) from partition 2 offset 8

Cleanup

  $ hgmo clean
