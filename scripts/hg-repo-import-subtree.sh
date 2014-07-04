#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Imports another hg repository into this one, placing it inside the chosen
# subdirectory, using a splice map to avoid non-linear history.
set -e

err() { echo $1; exit 1; }
prep-repo() {
  [ -n "$(hg qapplied --repository $1)" ] && err "Error: Patches applied in $1"
  hg pull --repository "$1"
}

[ $# -ne 2 ] && err "Usage: $(basename "$0") REPO-TO-IMPORT TARGET-SUBDIRECTORY"
SOURCE="$1"
SUBDIRECTORY="$2"

read -p "Import $SOURCE into the subdirectory $SUBDIRECTORY? (y/n)?"
[ "$REPLY" == "y" ] || exit 1

prep-repo "$PWD"
prep-repo "$SOURCE"

# Revisions for the splicemap (avoids having to rebase after import).
TARGET_TIP_REVISION=$(hg log -r default --template '{node}')
SOURCE_BASE_REVISION=$(hg log -r 0 --repository "$SOURCE" --template '{node}')

echo "rename . $SUBDIRECTORY" > ~filemap
echo "$SOURCE_BASE_REVISION $TARGET_TIP_REVISION" > ~splicemap
hg convert --filemap ~filemap --splicemap ~splicemap "$SOURCE" .
rm ~filemap ~splicemap

