#!/usr/bin/python3 -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function

import os
import subprocess
import sys

from configparser import ConfigParser

if "BROKER_ID" not in os.environ:
    print("error: BROKER_ID not in environment", file=sys.stderr)
    sys.exit(1)

if not os.path.exists("/etc/ssh/ssh_host_ed25519_key"):
    subprocess.check_call(
        [
            "/usr/bin/ssh-keygen",
            "-t",
            "ed25519",
            "-f",
            "/etc/ssh/ssh_host_ed25519_key",
            "-N",
            "",
        ]
    )

if not os.path.exists("/etc/ssh/ssh_host_rsa_key"):
    subprocess.check_call(
        [
            "/usr/bin/ssh-keygen",
            "-t",
            "rsa",
            "-b",
            "2048",
            "-f",
            "/etc/ssh/ssh_host_rsa_key",
            "-N",
            "",
        ]
    )

# Setup consumer group names
consumer_groupname = "hgweb%d" % (int(os.environ["BROKER_ID"]) - 1)
files = {
    "/etc/mercurial/vcsreplicator.ini",
    "/etc/mercurial/vcsreplicator-pending.ini",
}
for filename in files:
    parser = ConfigParser()
    parser.read(filename)

    parser.set("consumer", "client_id", consumer_groupname)
    parser.set("consumer", "group", consumer_groupname)

    with open(filename, "w") as f:
        parser.write(f)

subprocess.check_call(["/entrypoint-kafkabroker"])

os.execl(sys.argv[1], *sys.argv[1:])
