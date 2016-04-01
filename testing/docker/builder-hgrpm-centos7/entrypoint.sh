#!/bin/bash

set -e

rm -rf /hg-packages/*

cd /hg
hg pull

for version in ${HG_VERSIONS}
do
  hg --config extensions.purge= purge --all
  hg up ${version}
  make centos7
  cp -av packages/centos7/* /hg-packages/
done

exec "$@"
