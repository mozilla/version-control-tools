#!/bin/bash

set -e

rm -rf /hg-packages/*

cd /hg
hg pull

for version in ${HG_VERSIONS}
do
  hg --config extensions.purge= purge --all
  hg up ${version}
  make centos6
  cp -av packages/centos6/* /hg-packages/
done

exec "$@"
