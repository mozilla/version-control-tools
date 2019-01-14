#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

Create and seed repository

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)

  $ hg clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central > /dev/null
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push > /dev/null
  $ cd ..

Ensure bundle creation script raises during bundle generation

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles missing
  Traceback (most recent call last):
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in <module> (re)
      paths[repo] = generate_bundles(repo, upload=upload, **opts)
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in generate_bundles (re)
      hg_stat = os.stat(os.path.join(repo_full, '.hg'))
  OSError: [Errno 2] No such file or directory: '/repo/hg/mozilla/missing/.hg'
  [1]

And raises during upload since we don't have credentials in the test env

  $ hgmo exec hgssh sudo -u hg SINGLE_THREADED=1 /var/hg/venv_bundles/bin/python -u /var/hg/version-control-tools/scripts/generate-hg-s3-bundles mozilla-central
  tip is 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  1 changesets found
  1 changesets found
  writing 328 bytes for 3 files
  bundle requirements: generaldelta, revlogv1
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  uploading to s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  uploading to s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  uploading to s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  uploading to s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  uploading to s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  uploading to s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  uploading to s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  uploading to s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  uploading to s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  uploading to s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  uploading to s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  uploading to s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  Traceback (most recent call last):
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in <module> (re)
      paths[repo] = generate_bundles(repo, upload=upload, **opts)
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in generate_bundles (re)
      f.result()
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/concurrent/futures/_base.py", line \d+, in result (re)
      return self.__get_result()
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/concurrent/futures/thread.py", line \d+, in run (re)
      result = self.fn(*self.args, **self.kwargs)
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in upload_to_s3 (re)
      key.load()
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/boto3/resources/factory.py", line \d+, in do_action (re)
      response = action(self, *args, **kwargs)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/boto3/resources/action.py", line \d+, in __call__ (re)
      response = getattr(parent.meta.client, operation_name)(**params)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/client.py", line \d+, in _api_call (re)
      return self._make_api_call(operation_name, kwargs)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/client.py", line \d+, in _make_api_call (re)
      operation_model, request_dict)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/endpoint.py", line \d+, in make_request (re)
      return self._send_request(request_dict, operation_model)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/endpoint.py", line \d+, in _send_request (re)
      request = self.create_request(request_dict, operation_model)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/endpoint.py", line \d+, in create_request (re)
      operation_name=operation_model.name)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/hooks.py", line \d+, in emit (re)
      return self._emitter.emit(aliased_event_name, **kwargs) (hg48 !)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/hooks.py", line \d+, in emit (re) (hg48 !)
      return self._emit(event_name, kwargs)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/hooks.py", line \d+, in _emit (re)
      response = handler(**kwargs)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/signers.py", line \d+, in handler (re)
      return self.sign(operation_name, request)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/signers.py", line \d+, in sign (re)
      auth.add_auth(request)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/auth.py", line \d+, in add_auth (re)
      super(S3SigV4Auth, self).add_auth(request)
    File "/var/hg/venv_bundles/lib/python2.7/site-packages/botocore/auth.py", line \d+, in add_auth (re)
      raise NoCredentialsError
  botocore.exceptions.NoCredentialsError: Unable to locate credentials
  [1]

The manifest should be empty because there were no successful uploads

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  

An index.html and bundles.json document should be produced

  $ hgmo exec hgssh sudo -u hg SINGLE_THREADED=1 /var/hg/venv_bundles/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles mozilla-central --no-upload
  wrote synchronization message into replication log
  tip is 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  bundle already exists, skipping: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  bundle already exists, skipping: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  bundle already exists, skipping: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  $ hgmo exec hgssh ls /repo/hg/bundles
  bundles.json
  index.html
  lastrun
  mozilla-central
  repos

The clonebundles.manifest file should exist though

  $ hgmo exec hgssh ls /repo/hg/mozilla/mozilla-central/.hg/ | grep clonebundles
  clonebundles.manifest

Now do a fully working run

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles --no-upload mozilla-central >/dev/null
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

A subsequent bundle generation should produce a backup clonebundles.manifest.old file

  $ hgmo exec hgssh ls /repo/hg/mozilla/mozilla-central/.hg/ | grep clonebundles
  clonebundles.manifest
  clonebundles.manifest.old

The lastrun file should have been written with the last completion time.

  $ hgmo exec hgssh cat /repo/hg/bundles/lastrun
  \d+-\d+-\d+T\d+:\d+:\d+.\d+Z (re)

Cloning will fetch bundle

#if hg36

  $ hg --config experimental.clonebundles=true --config ui.clonebundlefallback=true clone -U ${HGWEB_0_URL}mozilla-central clonebundles-no-advertise
  applying clone bundle from https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.*.hg (glob)
  HTTP error fetching bundle: HTTP Error 404: Not Found
  falling back to normal clone
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 77538e1ce4be (hg44 !)

#endif

The full manifest is fetched normally

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=eu-central-1


Fetching with an AWS us-west-2 IP will limit to same region URLs

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

Fetching with a private IP and a cloud metadata file indicating host region is us-west-2 will limit to same region URLs

  $ http --no-headers --request-header "X-Cluster-Client-IP: 10.144.1.1" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

Fetching with an AWS IP from "other" region returns full list

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=eu-central-1


Fetching with a Mozilla IP prioritizes stream bundles.

  $ http --no-headers --request-header "X-Cluster-Client-IP: 64.213.97.192" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  

The copyfrom=x field copies bundles from another repo

  $ hgmo create-repo try scm_level_1
  (recorded repository creation in replication log)
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/try
  $ cd try
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push > /dev/null
  $ cd ..

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles --no-upload 'try copyfrom=mozilla-central'
  copying /repo/hg/mozilla/mozilla-central/.hg/clonebundles.manifest -> /repo/hg/mozilla/try/.hg/clonebundles.manifest
  ignoring repo try in index because no gzip bundle

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ http --no-headers ${HGWEB_0_URL}try?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=eu-central-1

zstd-max bundles created when requested

  $ cd mozilla-central
  $ echo ztd-max > foo
  $ hg commit -m zstd-max
  $ hg push >/dev/null
  $ cd ..
  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles 'mozilla-central zstd_max' --no-upload > /dev/null
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.packed1.hg BUNDLESPEC=none-packed1;requirements%3Dgeneraldelta%2Crevlogv1 ec2region=eu-central-1


  $ hgmo clean
