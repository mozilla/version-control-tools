# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import print_function, unicode_literals

import argparse
import os
import subprocess
import stat
import sys

from mach.decorators import (
    CommandArgument,
    CommandProvider,
    Command,
)


@CommandProvider
class HgmoCommands(object):
    def __init__(self, context):
        from vcttesting.docker import Docker, params_from_env
        from vcttesting.hgmo import HgCluster

        docker_url, tls = params_from_env(os.environ)
        docker = Docker(docker_url, tls=tls)
        if not docker.is_alive():
            print("Docker not available")
            sys.exit(1)
        self.c = HgCluster(docker)

    @Command("start", category="hgmo", description="Start a hg.mozilla.org cluster")
    @CommandArgument(
        "--master-ssh-port",
        type=int,
        help="Port number on which SSH server should listen",
    )
    @CommandArgument(
        "--show-output", action="store_true", help="Display output of shutdown process"
    )
    def start(self, master_ssh_port=None, show_output=False):
        s = self.c.start(master_ssh_port=master_ssh_port, show_output=show_output)
        print("SSH Hostname: %s" % s["master_ssh_hostname"])
        print("SSH Port: %s" % s["master_ssh_port"])
        print("LDAP URI: %s" % s["ldap_uri"])
        print("Web URL 0: %s" % s["hgweb_0_url"])
        print("Web URL 1: %s" % s["hgweb_1_url"])
        print("Pulse: %s:%d" % (s["pulse_hostname"], s["pulse_hostport"]))

    @Command("build", category="hgmo", description="Build hgmo test images")
    @CommandArgument("--image", type=str, help="Name of image to build")
    def build(self, image=None):
        from vcttesting.hgmo import HgCluster

        HgCluster.build(image=image)

    @Command(
        "shellinit",
        category="hgmo",
        description="Print shell commands to export variables",
    )
    def shellinit(self):
        cluster_state = self.c.get_state()

        print("export SSH_CID=%s" % cluster_state["master_id"])
        print("export PULSE_HOST=%s" % cluster_state["pulse_hostname"])
        print("export PULSE_PORT=%s" % cluster_state["pulse_hostport"])
        print("export SSH_SERVER=%s" % cluster_state["master_ssh_hostname"])
        print("export SSH_PORT=%d" % cluster_state["master_ssh_port"])
        # Don't export the full value because spaces.
        print(
            "export SSH_HOST_RSA_KEY=%s"
            % cluster_state["master_host_rsa_key"].split()[1]
        )
        print(
            "export SSH_HOST_ED25519_KEY=%s"
            % cluster_state["master_host_ed25519_key"].split()[1]
        )
        print("export HGWEB_0_URL=%s" % cluster_state["hgweb_0_url"])
        print("export HGWEB_1_URL=%s" % cluster_state["hgweb_1_url"])
        print("export HGWEB_0_CID=%s" % cluster_state["hgweb_0_cid"])
        print("export HGWEB_1_CID=%s" % cluster_state["hgweb_1_cid"])
        print("export KAFKA_0_HOSTPORT=%s" % cluster_state["kafka_0_hostport"])
        print("export KAFKA_1_HOSTPORT=%s" % cluster_state["kafka_1_hostport"])
        print("export KAFKA_2_HOSTPORT=%s" % cluster_state["kafka_2_hostport"])

    @Command(
        "clean", category="hgmo", description="Clean up all references to this cluster"
    )
    @CommandArgument(
        "--show-output", action="store_true", help="Display output of shutdown process"
    )
    def clean(self, show_output=False):
        self.c.clean(show_output=show_output)

    @Command(
        "create-ldap-user", category="hgmo", description="Create a new user in LDAP"
    )
    @CommandArgument("email", help="Email address associated with user")
    @CommandArgument("username", help="System account name")
    @CommandArgument("uid", type=int, help="Numeric user ID to associate with user")
    @CommandArgument("fullname", help="Full name of the user")
    @CommandArgument("--key-file", help="Use or create an SSH key")
    @CommandArgument(
        "--scm-level",
        type=int,
        choices=(1, 2, 3, 4),
        help="Add the user to the specified SCM level groups",
    )
    @CommandArgument(
        "--no-hg-access",
        action="store_true",
        help="Do not grant Mercurial access to user",
    )
    @CommandArgument("--hg-disabled", action="store_true", help="Set hgAccess to FALSE")
    @CommandArgument(
        "--group",
        action="append",
        dest="groups",
        help="Additional group to add the user to. (can be specified multiple times",
    )
    def create_ldap_user(
        self,
        email,
        username,
        uid,
        fullname,
        key_file=None,
        scm_level=None,
        no_hg_access=False,
        hg_disabled=False,
        groups=[],
    ):
        self.c.ldap.create_user(
            email,
            username,
            uid,
            fullname,
            key_filename=key_file,
            scm_level=scm_level,
            hg_access=not no_hg_access,
            hg_enabled=not hg_disabled,
            groups=groups,
        )

    @Command(
        "add-ssh-key", category="hgmo", description="Add an SSH public key to a user"
    )
    @CommandArgument("email", help="Email address of user to modify")
    @CommandArgument("key", help="SSH public key string")
    def add_ssh_key(self, email, key):
        if key == "-":
            key = sys.stdin.read().strip()
        self.c.ldap.add_ssh_key(email, key.encode("utf-8"))

    @Command(
        "add-user-to-group", category="hgmo", description="Add a user to an LDAP group"
    )
    @CommandArgument("email", help="Email address of user to modify")
    @CommandArgument("group", help="Name of LDAP group to add user to")
    def add_user_to_group(self, email, group):
        self.c.ldap.add_user_to_group(email, group)

    @Command(
        "create-repo", category="hgmo", description="Create a repository in the cluster"
    )
    @CommandArgument("name", help="Name of repository to create")
    @CommandArgument("group", default="scm_level_1", help="LDAP group that owns repo")
    def create_repo(self, name, group):
        out = self.c.create_repo(name, group=group)
        if out:
            sys.stdout.write(out)

    @Command(
        "aggregate-code-coverage",
        category="hgmo",
        description="Aggregate code coverage results to a directory",
    )
    @CommandArgument("destdir", help="Directory where to save code coverage files")
    def aggregate_code_coverage(self, destdir):
        self.c.aggregate_code_coverage(destdir)

    @Command(
        "exec", category="hgmo", description="Execute a command in a Docker container"
    )
    @CommandArgument(
        "--detach", action="store_true", help="Do not wait for process to finish"
    )
    @CommandArgument("name", help="Name of container to execute inside")
    @CommandArgument("command", help="Command to execute", nargs=argparse.REMAINDER)
    def execute(self, name, command, detach=False):
        state = self.c.get_state()

        if name == "hgssh":
            cid = state["master_id"]
        elif name == "pulse":
            cid = state["pulse_id"]
        elif name.startswith("hgweb"):
            i = int(name[5:])
            cid = state["hgweb_%d_cid" % i]
        else:
            print('invalid name. must be "hgssh" or "hgwebN"')
            return 1

        cmd = ["docker", "exec"]
        if "TESTTMP" not in os.environ:
            cmd.append("-it")
        if detach:
            cmd.append("-d")

        cmd.append(cid)
        cmd.extend(command)

        return subprocess.call(cmd)

    @Command(
        "download-mirror-ssh-keys",
        category="hgmo",
        description="Downloads SSH keys used by mirrors",
    )
    @CommandArgument("out_dir", help="Directory in which to write the keys")
    def download_mirror_ssh_keys(self, out_dir):
        state = self.c.get_state()
        priv, pub = self.c.get_mirror_ssh_keys(master_id=state["master_id"])[0:2]

        with open(os.path.join(out_dir, "mirror"), "w") as fh:
            fh.write(priv)
        os.chmod(os.path.join(out_dir, "mirror"), stat.S_IRUSR | stat.S_IWUSR)

        with open(os.path.join(out_dir, "mirror.pub"), "w") as fh:
            fh.write(pub)
        print("SSH keys written to %s" % out_dir)
