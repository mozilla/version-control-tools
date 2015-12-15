#require hgmodocker

  $ . $TESTDIR/pylib/vcsreplicator/tests/helpers.sh
  $ vcsrenv

  $ hgmo create-repo mozilla-central 1
  (recorded repository creation in replication log)
  $ standarduser

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push

  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer created Mercurial repository: $TESTTMP/repos/mozilla-central (glob)
  $ consumer --onetime
  $ consumer --onetime
  $ consumer --onetime
  * vcsreplicator.consumer pulling 1 heads (77538e1ce4bec5f7aac58a7ceca2da0e38e90a72) and 1 nodes from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  * vcsreplicator.consumer pulled 1 changesets into $TESTTMP/repos/mozilla-central (glob)

Corrupt the local repo

  $ echo corrupt > $TESTTMP/repos/mozilla-central/.hg/store/00manifest.i

  $ echo corrupt > foo
  $ hg commit -m 'push after mirror corrupted'
  $ hg -q push

  $ consumer --onetime
  $ consumer --onetime

Pulling into corrupt repo should result in abort

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    heads:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    name: hg-changegroup-1
    nodes:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    path: '{moz}/mozilla-central'
    source: serve

  $ consumer --onetime
  * vcsreplicator.consumer pulling 1 heads (0c6b2090d458675af812e445c8ab9b809e321f57) and 1 nodes from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  * vcsreplicator.consumer exiting main consume loop with error (glob)
  Traceback (most recent call last):
    File "*/bin/vcsreplicator-consumer", line *, in <module> (glob)
      load_entry_point('vcsreplicator', 'console_scripts', 'vcsreplicator-consumer')()
    File "*/vcsreplicator/consumer.py", line *, in cli (glob)
      consume(config, consumer, onetime=args.onetime)
    File "*/vcsreplicator/consumer.py", line *, in consume (glob)
      process_message(config, payload)
    File "*/vcsreplicator/consumer.py", line *, in process_message (glob)
      payload['heads'])
    File "*/vcsreplicator/consumer.py", line *, in process_hg_changegroup (glob)
      c.pull(source=url or 'default', rev=heads)
    File "*/hglib/client.py", line *, in pull (glob)
      self.rawcommand(args, eh=eh)
    File "*/hglib/client.py", line *, in rawcommand (glob)
      return eh(ret, out, err)
    File "*/hglib/util.py", line *, in __call__ (glob)
      raise error.CommandError(self.args, ret, out, err)
  hglib.error.CommandError: (255, 'pulling from ssh://*:$HGPORT/mozilla-central\nsearching for changes\nadding changesets\nadding manifests', 'transaction abort!\nrollback completed\nabort: index 00manifest.i unknown format 29298!') (glob)
  [1]

And the message should still be not consumed

  $ consumer --dump
  - _created: \d+\.\d+ (re)
    heads:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    name: hg-changegroup-1
    nodes:
    - 0c6b2090d458675af812e445c8ab9b809e321f57
    path: '{moz}/mozilla-central'
    source: serve

We should get the same failure if we try again

  $ consumer --onetime
  * vcsreplicator.consumer pulling 1 heads (0c6b2090d458675af812e445c8ab9b809e321f57) and 1 nodes from ssh://*:$HGPORT/mozilla-central into $TESTTMP/repos/mozilla-central (glob)
  * vcsreplicator.consumer exiting main consume loop with error (glob)
  Traceback (most recent call last):
    File "*/bin/vcsreplicator-consumer", line *, in <module> (glob)
      load_entry_point('vcsreplicator', 'console_scripts', 'vcsreplicator-consumer')()
    File "*/vcsreplicator/consumer.py", line *, in cli (glob)
      consume(config, consumer, onetime=args.onetime)
    File "*/vcsreplicator/consumer.py", line *, in consume (glob)
      process_message(config, payload)
    File "*/vcsreplicator/consumer.py", line *, in process_message (glob)
      payload['heads'])
    File "*/vcsreplicator/consumer.py", line *, in process_hg_changegroup (glob)
      c.pull(source=url or 'default', rev=heads)
    File "*/hglib/client.py", line *, in pull (glob)
      self.rawcommand(args, eh=eh)
    File "*/hglib/client.py", line *, in rawcommand (glob)
      return eh(ret, out, err)
    File "*/hglib/util.py", line *, in __call__ (glob)
      raise error.CommandError(self.args, ret, out, err)
  hglib.error.CommandError: (255, 'pulling from ssh://*:$HGPORT/mozilla-central\nsearching for changes\nadding changesets\nadding manifests', 'transaction abort!\nrollback completed\nabort: index 00manifest.i unknown format 29298!') (glob)
  [1]

We can skip over the message

  $ consumer --skip
  skipped message in partition 2 for group ttest

  $ consumer --onetime

Cleanuo

  $ hgmo clean
