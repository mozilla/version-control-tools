#!/bin/bash

if [ ! -e version-control-tools ]; then
  hg clone /version-control-tools version-control-tools
fi

cd version-control-tools
hg pull
hg --config extensions.purge= purge
hg up tip

./create-test-environment
source venv/bin/activate
./run-mercurial-tests.py -j4 --all-versions --cover
result=$?

rm -rf /version-control-tools/coverage
mv coverage/ /version-control-tools/

# Ideally this would be part of running tests. Until then, add it here
# so Jenkins doesn't bloat.
DOCKER_STATE_FILE=.docker-state.json testing/docker-control.py prune-images

exit $result
