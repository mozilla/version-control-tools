#!/bin/bash

set -e

if [ ! -e version-control-tools ]; then
  hg clone /version-control-tools version-control-tools
fi

cd version-control-tools
hg pull
hg --config extensions.purge= purge
hg up tip

./create-test-environment
source venv/bin/activate
./run-mercurial-tests.py -j4 --all-versions
