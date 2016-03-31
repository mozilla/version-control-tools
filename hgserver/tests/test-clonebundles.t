#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

Create and seed repository

  $ hgmo create-repo mozilla-central 1
  (recorded repository creation in replication log)

  $ hg clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central > /dev/null
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push > /dev/null
  $ cd ..

Ensure bundle creation script raises during bundle generation

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_tools/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles missing
  Traceback (most recent call last):
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in <module> (re)
      paths[repo] = generate_bundles(repo, upload=upload, **opts)
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in generate_bundles (re)
      hg_stat = os.stat(os.path.join(repo_full, '.hg'))
  OSError: [Errno 2] No such file or directory: '/repo/hg/mozilla/missing/.hg'
  [1]

And raises during upload since we don't have credentials in the test env

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_tools/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles mozilla-central
  writing /repo/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg.tmp
  stream bundle file written successully.
  include the following in its manifest entry:
  stream=revlogv1
  writing 328 bytes for 3 files
  bundle requirements: revlogv1
  1 changesets found
  tip is 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  uploading to s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg
  uploading to s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg
  uploading to s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  uploading to s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg
  uploading to s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg
  uploading to s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg
  Traceback (most recent call last):
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in <module> (re)
      paths[repo] = generate_bundles(repo, upload=upload, **opts)
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in generate_bundles (re)
      f.result()
    File "/var/hg/venv_tools/lib/python2.7/site-packages/concurrent/futures/_base.py", line \d+, in result (re)
      return self.__get_result()
    File "/var/hg/venv_tools/lib/python2.7/site-packages/concurrent/futures/thread.py", line \d+, in run (re)
      result = self.fn(*self.args, **self.kwargs)
    File "/var/hg/version-control-tools/scripts/generate-hg-s3-bundles", line \d+, in upload_to_s3 (re)
      c = S3Connection(host=host)
    File "/var/hg/venv_tools/lib/python2.7/site-packages/boto/s3/connection.py", line \d+, in __init__ (re)
      validate_certs=validate_certs, profile_name=profile_name)
    File "/var/hg/venv_tools/lib/python2.7/site-packages/boto/connection.py", line \d+, in __init__ (re)
      host, config, self.provider, self._required_auth_capability())
    File "/var/hg/venv_tools/lib/python2.7/site-packages/boto/auth.py", line \d+, in get_auth_handler (re)
      'Check your credentials' % (len(names), str(names)))
  boto.exception.NoAuthHandlerFound: No handler was ready to authenticate. 1 handlers were checked. ['HmacAuthV1Handler'] Check your credentials
  [1]

The manifest should be empty because there were no successful uploads

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  

Create a clonebundles manifest

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_tools/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles --no-upload mozilla-central &> /dev/null

Cloning will fetch bundle

#if hg36+

  $ hg --config experimental.clonebundles=true --config ui.clonebundlefallback=true clone -U ${HGWEB_0_URL}mozilla-central clonebundles-no-advertise
  applying clone bundle from https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg
  HTTP error fetching bundle: HTTP Error 403: Forbidden
  falling back to normal clone
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

#else

  $ hg --config extensions.bundleclone=$TESTDIR/hgext/bundleclone clone -U ${HGWEB_0_URL}mozilla-central bundleclone
  downloading bundle https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg
  abort: HTTP error fetching bundle: HTTP Error 403: Forbidden
  (consider contacting the server operator if this error persists)
  [255]

#endif

The full manifest is fetched normally

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-east-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-east-1

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=bundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg compression=gzip cdn=true requiresni=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg ec2region=us-west-2 compression=gzip
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg ec2region=us-west-1 compression=gzip
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg ec2region=us-east-1 compression=gzip
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg stream=revlogv1 cdn=true requiresni=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg ec2region=us-west-2 stream=revlogv1
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg ec2region=us-west-1 stream=revlogv1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg ec2region=us-east-1 stream=revlogv1

Fetching with an AWS us-west-2 IP will limit to same region URLs

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-2
  

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" ${HGWEB_0_URL}mozilla-central?cmd=bundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg ec2region=us-west-2 stream=revlogv1
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg ec2region=us-west-2 compression=gzip
  

Fetching with an AWS IP from "other" region returns full list

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-east-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-east-1

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" ${HGWEB_0_URL}mozilla-central?cmd=bundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg compression=gzip cdn=true requiresni=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg ec2region=us-west-2 compression=gzip
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg ec2region=us-west-1 compression=gzip
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg ec2region=us-east-1 compression=gzip
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg stream=revlogv1 cdn=true requiresni=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg ec2region=us-west-2 stream=revlogv1
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg ec2region=us-west-1 stream=revlogv1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-legacy.hg ec2region=us-east-1 stream=revlogv1

The copyfrom=x field copies bundles from another repo

  $ hgmo create-repo try 1
  (recorded repository creation in replication log)
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/try
  $ cd try
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg push > /dev/null
  $ cd ..

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_tools/bin/python /var/hg/version-control-tools/scripts/generate-hg-s3-bundles --no-upload 'try copyfrom=mozilla-central'
  copying /repo/hg/mozilla/mozilla-central/.hg/bundleclone.manifest -> /repo/hg/mozilla/try/.hg/bundleclone.manifest
  copying /repo/hg/mozilla/mozilla-central/.hg/clonebundles.manifest -> /repo/hg/mozilla/try/.hg/clonebundles.manifest
  $ http --no-headers ${HGWEB_0_URL}try?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-west-1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip.hg BUNDLESPEC=gzip-v1 ec2region=us-east-1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-west-1
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.packed1.hg BUNDLESPEC=none-packed1;requirements%3Drevlogv1 ec2region=us-east-1


  $ hgmo clean
