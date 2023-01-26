#!/usr/bin/python -u
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
import sys

os.environ["DOCKER_ENTRYPOINT"] = "1"

subprocess.check_call(
    ["ansible-playbook", "test-hgmaster.yml", "-c", "local", "-t", "docker-startup"],
    cwd="/vct/ansible",
)

del os.environ["DOCKER_ENTRYPOINT"]

# Generate host SSH keys for hg.
if not os.path.exists("/etc/mercurial/ssh/ssh_host_ed25519_key"):
    subprocess.check_call(
        [
            "/usr/bin/ssh-keygen",
            "-t",
            "ed25519",
            "-f",
            "/etc/mercurial/ssh/ssh_host_ed25519_key",
            "-N",
            "",
        ]
    )

if not os.path.exists("/etc/mercurial/ssh/ssh_host_rsa_key"):
    subprocess.check_call(
        [
            "/usr/bin/ssh-keygen",
            "-t",
            "rsa",
            "-b",
            "4096",
            "-f",
            "/etc/mercurial/ssh/ssh_host_rsa_key",
            "-N",
            "",
        ]
    )

subprocess.check_call(["/entrypoint-kafkabroker"])

os.execl(sys.argv[1], *sys.argv[1:])
