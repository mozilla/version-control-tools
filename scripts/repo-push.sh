#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This script is called during the changegroup hook via push-repo.sh.
# It fans out to registered Mercurial mirrors and executes a remote
# command via SSH telling repositories to pull changes.

ppid=$$
sshargs="-i /etc/mercurial/mirror -o ServerAliveInterval=5 -o ConnectionAttempts=3 -o StrictHostKeyChecking=no -o ConnectTimeout=10s -o PasswordAuthentication=no -o PreferredAuthentications=publickey -o UserKnownHostsFile=/etc/mercurial/known_hosts"

pulltrigger() {
    _args=$*
    /usr/bin/ssh -l hg ${sshargs} ${HOST} -- "${_args}" 2>&1 | \
        /usr/bin/logger -t "repo-push.sh[${ppid}] ${_args} to ${HOST} for ${SUDO_USER}"
    res=${PIPESTATUS[0]}
    if [ ${res} != 0 ]; then
    /usr/bin/logger -t "repo-push.sh[${ppid}] ssh returned ${res}, retrying ${_args} to ${HOST} for ${SUDO_USER}"
        sleep 1
    /usr/bin/ssh -l hg ${sshargs} ${HOST} -- "${_args}" 2>&1 | \
            /usr/bin/logger -t "repo-push.sh[${ppid}] retry ${_args} to ${HOST} for ${SUDO_USER}"
    fi
}

for HOST in $(cat /etc/mercurial/mirrors)
do
    pulltrigger $* &
done
wait
