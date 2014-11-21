#!/usr/bin/env bash
WHOAMI=$(id -un)
if [ "${WHOAMI}" == "hg" ]; then
    /usr/local/bin/repo-push.sh $(echo ${PWD/\/repo\/hg\/mozilla\/})
else
    sudo -u hg /usr/local/bin/repo-push.sh $(echo ${PWD/\/repo\/hg\/mozilla\/})
fi

