#!/bin/bash

if [ ! -e version-control-tools ]; then
  hg clone /version-control-tools version-control-tools
fi

cd version-control-tools
hg pull
hg --config extensions.purge= purge
hg up tip

# We always want to update BMO's source code as part of CI.
export FETCH_BMO=1

./create-test-environment
source venv/bin/activate
./run-tests -j2 --all-versions --cover
result=$?

rm -rf /version-control-tools/coverage
mv coverage/ /version-control-tools/

# Generate Sphinx documentation.
make -C docs html
rm -rf /version-control-tools/sphinx-docs
mv docs/_build /version-control-tools/sphinx-docs

# Ideally this would be part of running tests. Until then, add it here
# so Jenkins doesn't bloat.
# ./d0cker prune-images

exit $result
