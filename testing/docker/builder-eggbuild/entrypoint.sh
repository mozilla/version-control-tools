#!/bin/bash

set -e

PYTHON=/venv/bin/python

cd /version-control-tools/pylib/mozreview
$PYTHON setup.py bdist_egg

cd /version-control-tools/pylib/rbbz
$PYTHON setup.py bdist_egg

cd /version-control-tools/pylib/rbmozui
$PYTHON setup.py bdist_egg

cd /
unset PYTHON

exec "$@"
