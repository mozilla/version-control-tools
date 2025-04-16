  $ . $TESTDIR/hgext/hgmo/tests/helpers.sh

  $ startserver

  $ cd server
  $ touch foo
  $ hg -q commit -A -m initial
  $ cd ..

  $ hg -q clone http://localhost:$HGPORT repo
  $ cd repo

Put a clonebundles manifest in the repo

  $ cat > ../server/.hg/clonebundles.manifest << EOF
  > https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  > https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  > https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  > https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  > https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  > https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  > https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  > EOF

Clonebundles wire protocol command should return base manifest.

  $ http --no-headers http://localhost:$HGPORT?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
   (?)

  $ http --no-headers http://localhost:$HGPORT?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  

Fetching with an AWS us-west-2 IP will limit to same region URLs

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  
  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  

Fetching with a GCE IP will limit to GCE URL

  $ http --no-headers --request-header "X-Cluster-Client-IP: 8.34.212.1" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  
  $ http --no-headers --request-header "X-Cluster-Client-IP: 8.34.212.1" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  

Fetching with an Azure IP will limit to Azure URL.
  $ http --no-headers --request-header "X-Cluster-Client-IP: 40.70.147.2" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  

Fetching with an AWS IP from "other" region returns full list

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
   (?)

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  

Fetching with a Mozilla IP prioritizes stream bundles.

  $ http --no-headers --request-header "X-Cluster-Client-IP: 64.213.97.192" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  
  $ http --no-headers --request-header "X-Cluster-Client-IP: 64.213.97.192" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  

Fastly-Client-IP takes precedence over X-Cluster-Client-IP

  $ http --no-headers --request-header "X-Cluster-Client-IP: 8.34.212.1" --request-header "Fastly-Client-IP: 54.245.168.15" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  

  $ http --no-headers --request-header "X-Cluster-Client-IP: 8.34.212.1" --request-header "Fastly-Client-IP: 54.245.168.15" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  
ipv6 client from gcp us-central

  $ http --no-headers --request-header "Fastly-Client-IP: 2600:1900:4000::1" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  

ipv6 client from azure eastus2

  $ http --no-headers --request-header "Fastly-Client-IP: 2603:1030:40c:5::1" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  

other ipv6 client

  $ http --no-headers --request-header "Fastly-Client-IP: 2001:db8::1" http://localhost:$HGPORT/?cmd=clonebundles_manifest
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog ec2region=us-west-2
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog gceregion=us-west1
  https://mozhgeastus2.blob.core.windows.net/hgbundle/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Dgeneraldelta%2Crevlogv1%2Csparserevlog azureregion=eastus2
  

Confirm no errors in log

  $ cat ../server/error.log
