#require hgmodocker

  $ . $TESTDIR/hgserver/tests/helpers.sh
  $ hgmoenv
  $ standarduser

Create and seed repository

  $ hgmo create-repo mozilla-central scm_level_1
  (recorded repository creation in replication log)

  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/mozilla-central
  $ cd mozilla-central
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push
  $ cd ..

Ensure bundle creation script raises during bundle generation

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/generate-hg-s3-bundles missing
  abort: repository /repo/hg/mozilla/missing not found
  CalledProcessError: Command '['/var/hg/venv_bundles/bin/hg', '-R', '/repo/hg/mozilla/missing', 'log', '-r', 'tip', '-T', '{node}']' returned non-zero exit status 255.
  [1]

And raises during upload since we don't have credentials in the test env

  $ hgmo exec hgssh sudo -u hg SINGLE_THREADED=1 PYTHONUNBUFFERED=1 /var/hg/venv_bundles/bin/generate-hg-s3-bundles mozilla-central
  tip of mozilla-central is 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  running "/var/hg/venv_bundles/bin/hg --config 'extensions.vcsreplicator=!' -R /repo/hg/mozilla/mozilla-central bundle -a -t gzip-v2 /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg.tmp"
  1 changesets found
  bundle generated: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg (in *s) (glob)
  running "/var/hg/venv_bundles/bin/hg --config 'extensions.vcsreplicator=!' -R /repo/hg/mozilla/mozilla-central bundle -a -t zstd-v2 /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg.tmp"
  1 changesets found
  bundle generated: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg (in *s) (glob)
  running "/var/hg/venv_bundles/bin/hg --config 'extensions.vcsreplicator=!' -R /repo/hg/mozilla/mozilla-central bundle -a -t 'none-v2;stream=v2' /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg.tmp"
  bundle generated: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg (in *s) (glob)
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  uploading to s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg
  uploading to https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg
  uploading to https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg
  uploading to https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg
  uploading moz-hg-bundles-us-west-2:mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg from /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  uploading moz-hg-bundles-us-west-2:mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg from /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  uploading moz-hg-bundles-us-west-2:mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg from /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg
  NoCredentialsError: Unable to locate credentials
  [1]

The manifest should be empty because there were no successful uploads

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  
  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  
Remove fncache to test rebuilding code path

  $ hgmo exec hgssh rm /repo/hg/mozilla/mozilla-central/.hg/store/fncache

An index.html and bundles.json document should be produced

  $ hgmo exec hgssh sudo -u hg SINGLE_THREADED=1 /var/hg/venv_bundles/bin/generate-hg-s3-bundles mozilla-central --no-upload
  wrote synchronization message into replication log
  wrote heads synchronization message into replication log
  tip of mozilla-central is 77538e1ce4bec5f7aac58a7ceca2da0e38e90a72
  bundle already exists, skipping: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg
  bundle already exists, skipping: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg
  bundle already exists, skipping: /repo/hg/bundles/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg
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

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/generate-hg-s3-bundles --no-upload mozilla-central > /dev/null
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
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

Fetching with an AWS us-west-2 IP will limit to same region URLs

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

Fetching with a GCE IP will limit to GCE URL

  $ http --no-headers --request-header "X-Cluster-Client-IP: 8.34.212.1" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  

  $ http --no-headers --request-header "X-Cluster-Client-IP: 8.34.212.1" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  


Fetching with a private IP and a cloud metadata file indicating host region is us-west-2 in AWS will limit to same region URLs
Reload apache after setting config, so processes pick up the new config

  $ hgmo exec hgweb0 /set-config-option /etc/mercurial/hgrc hgmo "instance-data-path" "/var/hg/test_instance_data.json"
  $ hgmo exec hgweb0 supervisorctl restart httpd
  httpd: stopped
  httpd: started
  $ http --no-headers --request-header "Remote-Addr: 10.144.1.1" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

  $ http --no-headers --request-header "Remote-Addr: 10.144.1.1" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

  $ hgmo exec hgweb0 /set-config-option /etc/mercurial/hgrc hgmo "instance-data-path" ""
  $ hgmo exec hgweb0 supervisorctl restart httpd
  httpd: stopped
  httpd: started

Fetching with an AWS IP from "other" region returns full list

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

Fetching with a Mozilla IP prioritizes stream bundles.

  $ http --no-headers --request-header "X-Cluster-Client-IP: 64.213.97.192" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

  $ http --no-headers --request-header "X-Cluster-Client-IP: 64.213.97.192" ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

The copyfrom=x field copies bundles from another repo

  $ hgmo create-repo try scm_level_1
  (recorded repository creation in replication log)
  $ hg -q clone ssh://${SSH_SERVER}:${SSH_PORT}/try
  $ cd try
  $ touch foo
  $ hg -q commit -A -m initial
  $ hg -q push
  $ cd ..

  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/generate-hg-s3-bundles --no-upload 'try copyfrom=mozilla-central'
  copying /repo/hg/mozilla/mozilla-central/.hg/clonebundles.manifest -> /repo/hg/mozilla/try/.hg/clonebundles.manifest
  ignoring repo try in index because no gzip bundle
  $ hgmo exec hgssh /var/hg/venv_bundles/bin/hg -R /repo/hg/mozilla/try replicatesync
  wrote synchronization message into replication log
  wrote heads synchronization message into replication log

  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini
  $ http --no-headers ${HGWEB_0_URL}try?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

  $ http --no-headers ${HGWEB_0_URL}try?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

zstd-max bundles created when requested

  $ cd mozilla-central
  $ echo ztd-max > foo
  $ hg commit -m zstd-max
  $ hg -q push
  $ cd ..
  $ hgmo exec hgssh sudo -u hg /var/hg/venv_bundles/bin/generate-hg-s3-bundles 'mozilla-central zstd_max' --no-upload > /dev/null
  $ hgmo exec hgweb0 /var/hg/venv_replication/bin/vcsreplicator-consumer --wait-for-no-lag /etc/mercurial/vcsreplicator.ini

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

  $ http --no-headers ${HGWEB_0_URL}mozilla-central?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.zstd-max.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://storage.googleapis.com/moz-hg-bundles-gcp-na-ne1/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=northamerica-northeast1
  https://mozhgwestus3.blob.core.windows.net/hgbundle/mozilla-central/6ed7c1ea69ee8362d21174681a219d1a9e7aad52.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore azureregion=westus3
  

Print some logs

  $ hgmo exec hgweb0 cat /var/log/httpd/hg.mozilla.org/error_log

  $ hgmo clean
