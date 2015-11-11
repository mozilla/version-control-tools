#!/bin/bash

# Build modern Python from source because Ubuntu 14.04 ships with an
# older one that doesn't support modern SSL and this screws up packaging
# foo.
if [ ! -e ~/.pyenv ]; then
  git clone https://github.com/yyuu/pyenv.git ~/.pyenv
fi
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

if [ ! -e ~/.pyenv/versions/2.7.10 ]; then
  pyenv install 2.7.10
  pyenv rehash
fi

pyenv shell 2.7.10
pip install --upgrade pip virtualenv

# Install a modern Mercurial or we may run into issues cloning from the mounted
# repo since it may be using settings not known by the older Mercurial
# installed by Ubuntu.
pip install --upgrade Mercurial

if [ ! -e ~/version-control-tools ]; then
  hg clone --pull /version-control-tools ~/version-control-tools
fi

cd ~/version-control-tools
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
