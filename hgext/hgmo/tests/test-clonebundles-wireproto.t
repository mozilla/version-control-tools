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
  > https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  > https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  > https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  > https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  > https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  > https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  > https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  > https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  > https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  > https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  > https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  > https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  > https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-1
  > https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-2
  > https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-1
  > https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=eu-central-1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  > https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  > EOF

Clonebundles wire protocol command should return base manifest.

  $ http --no-headers http://localhost:$HGPORT?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1


Fetching with an AWS us-west-2 IP will limit to same region URLs

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.245.168.15" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  

Fetching with a GCE IP will limit to GCE URL

  $ http --no-headers --request-header "X-Cluster-Client-IP: 8.34.212.1" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  

Fetching with an AWS IP from "other" region returns full list

  $ http --no-headers --request-header "X-Cluster-Client-IP: 54.248.220.10" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1


Fetching with a Mozilla IP prioritizes stream bundles.

  $ http --no-headers --request-header "X-Cluster-Client-IP: 64.213.97.192" http://localhost:$HGPORT/?cmd=clonebundles
  200
  
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.stream-v2.hg BUNDLESPEC=none-v2;stream=v2;requirements%3Ddotencode%2Cfncache%2Cgeneraldelta%2Crevlogv1%2Csparserevlog%2Cstore gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.zstd.hg BUNDLESPEC=zstd-v2 gceregion=us-west1
  https://hg.cdn.mozilla.net/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 REQUIRESNI=true cdn=true
  https://s3-us-west-2.amazonaws.com/moz-hg-bundles-us-west-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-2
  https://s3-us-west-1.amazonaws.com/moz-hg-bundles-us-west-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-west-1
  https://s3-us-east-2.amazonaws.com/moz-hg-bundles-us-east-2/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-2
  https://s3-external-1.amazonaws.com/moz-hg-bundles-us-east-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=us-east-1
  https://s3-eu-central-1.amazonaws.com/moz-hg-bundles-eu-central-1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 ec2region=eu-central-1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-central1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-central1
  https://storage.googleapis.com/moz-hg-bundles-gcp-us-west1/mozilla-central/77538e1ce4bec5f7aac58a7ceca2da0e38e90a72.gzip-v2.hg BUNDLESPEC=gzip-v2 gceregion=us-west1
  

Confirm no errors in log

  $ cat ../server/error.log
