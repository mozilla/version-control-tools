#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is ran as a changegroup hook for telling mirrors to sync repos.

WHOAMI=$(id -un)
if [ "${WHOAMI}" == "hg" ]; then
    /usr/local/bin/repo-push.sh $(echo ${PWD/\/repo\/hg\/mozilla\/})
else
    sudo -u hg /usr/local/bin/repo-push.sh $(echo ${PWD/\/repo\/hg\/mozilla\/})
fi
